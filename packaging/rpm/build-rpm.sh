#!/bin/bash
# build-rpm.sh - build the .rpm for Fedora/openSUSE/RHEL.
# Uses the distro's PyQt6 (python3-qt6) like the .deb; vendors only vdf.
set -euo pipefail

cd "$(dirname "$0")/../.."

VERSION=$(python3 -c "exec(open('easy_scsmodmanager/__init__.py').read()); print(__version__)")

echo "Building .rpm for Easy SCSModManager v${VERSION}..."

mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Source tarball matching Source0 (git archive is not available in containers)
tar czf ~/rpmbuild/SOURCES/easy-scsmodmanager-${VERSION}.tar.gz \
    --transform "s,^\\.,easy-scsmodmanager-${VERSION}," \
    --exclude='.git' --exclude='dist' --exclude='build' \
    --exclude='__pycache__' --exclude='*.egg-info' \
    .

# Spec with the measured version substituted in
sed "s/^Version:.*/Version:        ${VERSION}/" \
    packaging/rpm/easy-scsmodmanager.spec > ~/rpmbuild/SPECS/easy-scsmodmanager.spec

rpmbuild -ba ~/rpmbuild/SPECS/easy-scsmodmanager.spec

echo ""
echo "RPMs in ~/rpmbuild/RPMS/noarch/:"
ls -lh ~/rpmbuild/RPMS/noarch/ 2>/dev/null || true
