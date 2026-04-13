-module(demo_support).

-export([
    setup/1,
    listen/1,
    accept/1,
    read_request/1,
    send_json/4,
    close/1,
    now_rfc3339/0,
    mnesia_upsert_feature/5,
    mnesia_get_feature/2,
    mnesia_list_features/0
]).

-define(TABLE, feature_toggle).

setup(Dir0) ->
    Dir = filename:absname(Dir0),
    ok = ensure_mnesia_dir(Dir),
    application:load(mnesia),
    ok = application:set_env(mnesia, dir, Dir),
    ensure_schema(Dir),
    ok = mnesia:start(),
    ok = ensure_table(),
    ok.

listen(Port) ->
    {ok, ListenSocket} = gen_tcp:listen(Port, [binary, {packet, raw}, {active, false}, {reuseaddr, true}]),
    ListenSocket.

accept(ListenSocket) ->
    {ok, Socket} = gen_tcp:accept(ListenSocket),
    Socket.

close(Socket) ->
    gen_tcp:close(Socket).

read_request(Socket) ->
    case recv_until_headers(Socket, <<>>) of
        {ok, HeaderBin, Rest} ->
            ContentLength = content_length(HeaderBin),
            case recv_body(Socket, Rest, ContentLength) of
                {ok, BodyBin} ->
                    parse_request(HeaderBin, BodyBin);
                {error, closed} ->
                    error_request("connection_closed");
                {error, Reason} ->
                    error_request(io_lib:format("read_body_error: ~p", [Reason]))
            end;
        {error, closed} ->
            error_request("connection_closed");
        {error, Reason} ->
            error_request(io_lib:format("read_headers_error: ~p", [Reason]))
    end.

send_json(Socket, Status, Payload, JsonArray) ->
    JsonReady = json_ready(Payload, JsonArray),
    Body = iolist_to_binary(json:encode(JsonReady)),
    Response = [
        "HTTP/1.1 ", status_line(Status), "\r\n",
        "content-type: application/json\r\n",
        "content-length: ", integer_to_list(byte_size(Body)), "\r\n",
        "connection: close\r\n",
        "\r\n",
        Body
    ],
    gen_tcp:send(Socket, Response).

now_rfc3339() ->
    calendar:system_time_to_rfc3339(erlang:system_time(second), [{unit, second}]).

mnesia_upsert_feature(Name, Environment, Enabled, Description, UpdatedAt) ->
    Fun =
        fun() ->
            Record = {
                ?TABLE,
                {Name, Environment},
                Name,
                Environment,
                Enabled,
                Description,
                UpdatedAt
            },
            ok = mnesia:write(Record),
            feature_record_to_map(Record)
        end,
    {atomic, Feature} = mnesia:transaction(Fun),
    Feature.

mnesia_get_feature(Name, Environment) ->
    Fun =
        fun() ->
            case mnesia:read(?TABLE, {Name, Environment}) of
                [Record] -> feature_record_to_map(Record);
                [] -> undefined
            end
        end,
    {atomic, Result} = mnesia:transaction(Fun),
    case Result of
        undefined -> undefined;
        Feature -> Feature
    end.

mnesia_list_features() ->
    Fun =
        fun() ->
            Fold =
                fun(Record, Acc) ->
                    [feature_record_to_map(Record) | Acc]
                end,
            mnesia:foldl(Fold, [], ?TABLE)
        end,
    {atomic, Features} = mnesia:transaction(Fun),
    lists:sort(
        fun(A, B) ->
            {maps:get(environment, A), maps:get(name, A)} =< {maps:get(environment, B), maps:get(name, B)}
        end,
        Features
    ).

ensure_mnesia_dir(Dir) ->
    ok = filelib:ensure_path(filename:join(Dir, "placeholder")),
    ok.

ensure_schema(Dir) ->
    case filelib:is_file(filename:join(Dir, "schema.DAT")) of
        true ->
            ok;
        false ->
            case mnesia:create_schema([node()]) of
                ok -> ok;
                {error, {_, {already_exists, _}}} -> ok;
                {error, {already_exists, _}} -> ok
            end
    end.

ensure_table() ->
    Attrs = [key, name, environment, enabled, description, updated_at],
    case mnesia:create_table(?TABLE, [
        {attributes, Attrs},
        {type, set},
        {disc_copies, [node()]}
    ]) of
        {atomic, ok} ->
            ok;
        {aborted, {already_exists, ?TABLE}} ->
            ok
    end,
    ok = mnesia:wait_for_tables([?TABLE], 5000),
    ok.

recv_until_headers(Socket, Acc) ->
    case binary:match(Acc, <<"\r\n\r\n">>) of
        {Pos, 4} ->
            <<Headers:Pos/binary, _Sep:4/binary, Rest/binary>> = Acc,
            {ok, Headers, Rest};
        nomatch ->
            case gen_tcp:recv(Socket, 0, 5000) of
                {ok, Chunk} ->
                    recv_until_headers(Socket, <<Acc/binary, Chunk/binary>>);
                Error ->
                    Error
            end
    end.

recv_body(_Socket, Rest, ContentLength) when byte_size(Rest) >= ContentLength ->
    <<Body:ContentLength/binary, _/binary>> = Rest,
    {ok, Body};
recv_body(Socket, Rest, ContentLength) ->
    Missing = ContentLength - byte_size(Rest),
    case gen_tcp:recv(Socket, Missing, 5000) of
        {ok, Chunk} ->
            recv_body(Socket, <<Rest/binary, Chunk/binary>>, ContentLength);
        Error ->
            Error
    end.

parse_request(HeaderBin, BodyBin) ->
    case binary:split(HeaderBin, <<"\r\n">>, [global]) of
        [RequestLineBin | _HeaderLines] ->
            parse_request_line(RequestLineBin, BodyBin);
        _ ->
            error_request("invalid_http_request")
    end.

parse_request_line(RequestLineBin, BodyBin) ->
    case binary:split(RequestLineBin, <<" ">>, [global]) of
        [MethodBin, TargetBin, _VersionBin] ->
            {PathBin, QueryBin} = split_target(TargetBin),
            Path = binary_to_list(PathBin),
            FeatureName = feature_name_from_path(PathBin),
            Environment = query_param(QueryBin, <<"environment">>),
            build_request(binary_to_list(MethodBin), Path, FeatureName, Environment, BodyBin);
        _ ->
            error_request("invalid_request_line")
    end.

build_request(Method, Path, FeatureName, Environment, <<>>) ->
    #{
        method => Method,
        path => Path,
        feature_name => FeatureName,
        environment => Environment,
        body => undefined,
        parse_error => undefined
    };
build_request(Method, Path, FeatureName, Environment, BodyBin) ->
    try
        Decoded = json:decode(BodyBin),
        Body = normalize_feature_payload(Decoded),
        #{
            method => Method,
            path => Path,
            feature_name => FeatureName,
            environment => Environment,
            body => Body,
            parse_error => undefined
        }
    catch
        error:_ ->
            #{
                method => Method,
                path => Path,
                feature_name => FeatureName,
                environment => Environment,
                body => undefined,
                parse_error => "invalid_json_body"
            }
    end.

error_request(Message) ->
    #{
        method => "UNKNOWN",
        path => "/",
        feature_name => undefined,
        environment => undefined,
        body => undefined,
        parse_error => flatten(Message)
    }.

split_target(TargetBin) ->
    case binary:split(TargetBin, <<"?">>) of
        [PathBin, QueryBin] -> {PathBin, QueryBin};
        [PathBin] -> {PathBin, <<>>}
    end.

feature_name_from_path(<<"/features/", Name/binary>>) when byte_size(Name) > 0 ->
    binary_to_list(Name);
feature_name_from_path(_) ->
    undefined.

query_param(<<>>, _Key) ->
    undefined;
query_param(QueryBin, Key) ->
    Pairs = binary:split(QueryBin, <<"&">>, [global]),
    query_param_from_pairs(Pairs, Key).

query_param_from_pairs([], _Key) ->
    undefined;
query_param_from_pairs([Pair | Rest], Key) ->
    case binary:split(Pair, <<"=">>) of
        [Key, Value] -> binary_to_list(Value);
        _ -> query_param_from_pairs(Rest, Key)
    end.

content_length(HeaderBin) ->
    HeaderLines = binary:split(HeaderBin, <<"\r\n">>, [global]),
    find_content_length(HeaderLines).

find_content_length([]) ->
    0;
find_content_length([Line | Rest]) ->
    case binary:split(Line, <<":">>) of
        [Name, Value] ->
            case lower_binary(trim_binary(Name)) of
                <<"content-length">> ->
                    binary_to_integer(trim_binary(Value));
                _ ->
                    find_content_length(Rest)
            end;
        _ ->
            find_content_length(Rest)
    end.

normalize_feature_payload(Map) when is_map(Map) ->
    #{
        name => required_string(Map, <<"name">>),
        environment => required_string(Map, <<"environment">>),
        enabled => maps:get(<<"enabled">>, Map, undefined),
        description => optional_string(Map, <<"description">>)
    };
normalize_feature_payload(_) ->
    undefined.

required_string(Map, Key) ->
    case maps:get(Key, Map, undefined) of
        Value when is_binary(Value) -> binary_to_list(Value);
        _ -> undefined
    end.

optional_string(Map, Key) ->
    case maps:get(Key, Map, undefined) of
        Value when is_binary(Value) -> binary_to_list(Value);
        null -> undefined;
        undefined -> undefined;
        _ -> undefined
    end.

feature_record_to_map({?TABLE, _Key, Name, Environment, Enabled, Description, UpdatedAt}) ->
    #{
        name => Name,
        environment => Environment,
        enabled => Enabled,
        description => Description,
        updated_at => UpdatedAt
    }.

json_ready(Value, true) when is_list(Value) ->
    [json_ready(Item, false) || Item <- Value];
json_ready(Value, false) when is_list(Value) ->
    case is_string_list(Value) of
        true -> unicode:characters_to_binary(Value);
        false -> [json_ready(Item, false) || Item <- Value]
    end;
json_ready(Value, _TopArray) when is_map(Value) ->
    maps:from_list([
        {json_key(Key), json_ready(Item, false)}
        || {Key, Item} <- maps:to_list(Value)
    ]);
json_ready(undefined, _TopArray) ->
    null;
json_ready(Value, _TopArray) ->
    Value.

json_key(Key) when is_atom(Key) ->
    Key;
json_key(Key) when is_list(Key) ->
    unicode:characters_to_binary(Key);
json_key(Key) ->
    Key.

is_string_list([]) ->
    false;
is_string_list(List) ->
    io_lib:printable_unicode_list(List).

status_line(200) -> "200 OK";
status_line(400) -> "400 Bad Request";
status_line(404) -> "404 Not Found";
status_line(405) -> "405 Method Not Allowed";
status_line(500) -> "500 Internal Server Error";
status_line(_) -> "500 Internal Server Error".

trim_binary(Bin) ->
    list_to_binary(string:trim(binary_to_list(Bin))).

lower_binary(Bin) ->
    list_to_binary(string:lowercase(binary_to_list(Bin))).

flatten(Value) ->
    lists:flatten(io_lib:format("~ts", [Value])).
