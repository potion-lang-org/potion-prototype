#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PACKAGE_NAME="potion-lang"
BUILD_DIR="${PROJECT_ROOT}/dist"
DEB_BUILD_ROOT="${PROJECT_ROOT}/dist/deb"

check_command() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "Erro: comando '$1' não encontrado. Instale-o e tente novamente." >&2
        exit 1
    }
}

echo "==> Verificando dependências do sistema..."
check_command python3
check_command dpkg-deb

echo "==> Limpando diretórios anteriores..."
rm -rf "${DEB_BUILD_ROOT}"
mkdir -p "${DEB_BUILD_ROOT}/DEBIAN"
mkdir -p "${DEB_BUILD_ROOT}/usr/bin"
mkdir -p "${DEB_BUILD_ROOT}/usr/lib/${PACKAGE_NAME}/site-packages"
mkdir -p "${DEB_BUILD_ROOT}/usr/share/doc/${PACKAGE_NAME}"
mkdir -p "${BUILD_DIR}"

echo "==> Copiando módulos Python para o diretório de controle..."
cp -R "${PROJECT_ROOT}/cli" "${DEB_BUILD_ROOT}/usr/lib/${PACKAGE_NAME}/site-packages/"
cp -R "${PROJECT_ROOT}/codegen" "${DEB_BUILD_ROOT}/usr/lib/${PACKAGE_NAME}/site-packages/"
cp -R "${PROJECT_ROOT}/lexer" "${DEB_BUILD_ROOT}/usr/lib/${PACKAGE_NAME}/site-packages/"
cp -R "${PROJECT_ROOT}/parser" "${DEB_BUILD_ROOT}/usr/lib/${PACKAGE_NAME}/site-packages/"
cp -R "${PROJECT_ROOT}/semantic" "${DEB_BUILD_ROOT}/usr/lib/${PACKAGE_NAME}/site-packages/"
find "${DEB_BUILD_ROOT}/usr/lib/${PACKAGE_NAME}/site-packages" -type d -name "__pycache__" -prune -exec rm -rf {} +

cp "${PROJECT_ROOT}/README.md" "${DEB_BUILD_ROOT}/usr/share/doc/${PACKAGE_NAME}/"
cp "${PROJECT_ROOT}/README-pt-br.md" "${DEB_BUILD_ROOT}/usr/share/doc/${PACKAGE_NAME}/"
cp "${PROJECT_ROOT}/LICENSE" "${DEB_BUILD_ROOT}/usr/share/doc/${PACKAGE_NAME}/copyright"

echo "==> Criando wrapper 'potionc'..."
cat > "${DEB_BUILD_ROOT}/usr/bin/potionc" <<'EOF'
#!/usr/bin/env bash
PYTHON_EXEC="/usr/bin/python3"
SITE_PACKAGES="/usr/lib/potion-lang/site-packages"
export PYTHONPATH="${SITE_PACKAGES}${PYTHONPATH:+:${PYTHONPATH}}"
exec "$PYTHON_EXEC" -m cli.potionc "$@"
EOF
chmod +x "${DEB_BUILD_ROOT}/usr/bin/potionc"

echo "==> Gerando metadata DEBIAN/control..."
cat > "${DEB_BUILD_ROOT}/DEBIAN/control" <<EOF
Package: ${PACKAGE_NAME}
Version: 0.1.0
Section: utils
Priority: optional
Architecture: all
Maintainer: Willians Costa da Silva <willianscsilva@gmail.com>
Depends: python3 (>= 3.8), erlang
Description: Potion Language compiler and CLI
 Minimal language that targets Erlang/OTP, providing a CLI 'potionc'.
EOF

echo "==> Ajustando permissões..."
chmod -R go-w "${DEB_BUILD_ROOT}"

DEB_OUTPUT="${BUILD_DIR}/${PACKAGE_NAME}_0.1.0_all.deb"
echo "==> Construindo pacote .deb em ${DEB_OUTPUT}..."
dpkg-deb --build "${DEB_BUILD_ROOT}" "${DEB_OUTPUT}"

echo "Pacote .deb gerado em ${DEB_OUTPUT}"
