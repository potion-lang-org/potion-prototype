#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PACKAGE_NAME="potion-lang"
VERSION="0.1.0"
BUILD_DIR="${PROJECT_ROOT}/dist"
RPMBUILD_ROOT="${PROJECT_ROOT}/dist/rpmbuild"

check_command() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "Erro: comando '$1' não encontrado. Instale-o e tente novamente." >&2
        exit 1
    }
}

echo "==> Verificando dependências do sistema..."
check_command python3
check_command rpmbuild

mkdir -p "${BUILD_DIR}"

echo "==> Limpando diretórios anteriores..."
rm -rf "${RPMBUILD_ROOT}"
mkdir -p "${RPMBUILD_ROOT}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

echo "==> Gerando distribuição Python..."
(
    cd "${PROJECT_ROOT}"
    python3 setup.py sdist --dist-dir "${BUILD_DIR}" >/dev/null
)
SDIST_PATH=$(find "${BUILD_DIR}" -maxdepth 1 -type f \( -name "${PACKAGE_NAME}-${VERSION}.tar.gz" -o -name "${PACKAGE_NAME//-/_}-${VERSION}.tar.gz" \) -print -quit)
if [ -z "${SDIST_PATH:-}" ] || [ ! -f "${SDIST_PATH}" ]; then
    echo "Erro: arquivo sdist não encontrado em ${BUILD_DIR}." >&2
    exit 1
fi
cp "${SDIST_PATH}" "${RPMBUILD_ROOT}/SOURCES/"

echo "==> Criando spec file..."
cat > "${RPMBUILD_ROOT}/SPECS/${PACKAGE_NAME}.spec" <<EOF
Name:           ${PACKAGE_NAME}
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        Potion Language compiler and CLI

License:        MIT
URL:            https://github.com/potion-lang-org/potion
Source0:        $(basename "${SDIST_PATH}")

BuildArch:      noarch
BuildRequires:  python3-devel, python3-setuptools
Requires:       python3 >= 3.8, erlang

%description
Potion é uma linguagem minimalista focada em gerar código Erlang, fornecendo a CLI 'potionc'.

%prep
%setup -q

%build
%py3_build

%install
rm -rf %{buildroot}
%py3_install

%files
%license LICENSE
%doc README.md README-pt-br.md
%{_bindir}/potionc
%{python3_sitelib}/cli/
%{python3_sitelib}/codegen/
%{python3_sitelib}/lexer/
%{python3_sitelib}/parser/
%{python3_sitelib}/semantic/
%{python3_sitelib}/potion_lang-*.dist-info/

%changelog
* Wed Sep 21 2025 Willians Costa da Silva <willianscsilva@gmail.com> - ${VERSION}-1
- RPM inicial do Potion Language.
EOF

echo "==> Construindo pacote RPM..."
rpmbuild --define "_topdir ${RPMBUILD_ROOT}" -ba "${RPMBUILD_ROOT}/SPECS/${PACKAGE_NAME}.spec"

RPM_PATH=$(find "${RPMBUILD_ROOT}/RPMS" -name "${PACKAGE_NAME}-${VERSION}-1*.rpm" -print -quit)
echo "Pacote .rpm gerado em ${RPM_PATH}"
