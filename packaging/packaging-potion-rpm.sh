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

echo "==> Limpando diretórios anteriores..."
rm -rf "${RPMBUILD_ROOT}"
mkdir -p "${RPMBUILD_ROOT}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

echo "==> Gerando distribuição Python..."
python3 -m build --sdist --wheel --outdir "${BUILD_DIR}" >/dev/null
SDIST_PATH=$(ls "${BUILD_DIR}"/${PACKAGE_NAME}-${VERSION}.tar.gz)
cp "${SDIST_PATH}" "${RPMBUILD_ROOT}/SOURCES/"

echo "==> Criando spec file..."
cat > "${RPMBUILD_ROOT}/SPECS/${PACKAGE_NAME}.spec" <<EOF
Name:           ${PACKAGE_NAME}
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        Potion Language compiler and CLI

License:        Apache-2.0
URL:            https://github.com/potion-lang-org/potion
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel, python3-setuptools
Requires:       python3 >= 3.10, erlang

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
%{python3_sitelib}/potion_lang*

%changelog
* Wed Sep 21 2025 Willians Costa da Silva <willianscsilva@gmail.com> - ${VERSION}-1
- RPM inicial do Potion Language.
EOF

echo "==> Construindo pacote RPM..."
rpmbuild --define "_topdir ${RPMBUILD_ROOT}" -ba "${RPMBUILD_ROOT}/SPECS/${PACKAGE_NAME}.spec"

RPM_PATH=$(find "${RPMBUILD_ROOT}/RPMS" -name "${PACKAGE_NAME}-${VERSION}-1*.rpm" -print -quit)
echo "Pacote .rpm gerado em ${RPM_PATH}"
