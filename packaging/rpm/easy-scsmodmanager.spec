%global app_id io.github.switch_bros.EasySCSModManager

Name:           easy-scsmodmanager
Version:        1.1.2
Release:        1%{?dist}
Summary:        Mod and profile manager for Euro Truck Simulator 2 and ATS

License:        GPL-3.0-or-later
URL:            https://github.com/Switch-Bros/easy-scsmodmanager
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-build
BuildRequires:  python3-installer
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel
BuildRequires:  python3-pip

Requires:       python3 >= 3.13
Requires:       python3-qt6
Requires:       python3-pillow
Requires:       python3-pycryptodome
Requires:       python3-httpx

%description
Looks like the in-game mod manager but adds search, drag and drop activation,
grouped load order with compatibility and conflict hints, map combo
export/import, favourites, profile backup/restore and an ETS2/ATS switcher.
Fully bilingual (English/German).

%prep
%autosetup -n easy-scsmodmanager-%{version}

%build
python3 -m build --wheel --no-isolation

%install
python3 -m installer --destdir=%{buildroot} dist/*.whl

# vdf is not packaged by Fedora; vendor it next to the app like the .deb does
pip3 install --target=%{buildroot}%{python3_sitelib} vdf --no-deps

# Desktop entry
install -Dm644 easy_scsmodmanager/resources/%{app_id}.desktop \
    %{buildroot}%{_datadir}/applications/%{app_id}.desktop

# Icons
install -Dm644 easy_scsmodmanager/resources/icon.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/%{app_id}.svg
install -Dm644 easy_scsmodmanager/resources/icon.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{app_id}.png

# Metainfo
install -Dm644 easy_scsmodmanager/resources/%{app_id}.metainfo.xml \
    %{buildroot}%{_datadir}/metainfo/%{app_id}.metainfo.xml

# License
install -Dm644 LICENSE %{buildroot}%{_datadir}/licenses/%{name}/LICENSE

%files
%license LICENSE
%{_bindir}/easy-scsmodmanager
%{python3_sitelib}/easy_scsmodmanager/
%{python3_sitelib}/easy_scsmodmanager-*.dist-info/
%{python3_sitelib}/vdf/
%{python3_sitelib}/vdf-*.dist-info/
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{app_id}.svg
%{_datadir}/icons/hicolor/512x512/apps/%{app_id}.png
%{_datadir}/metainfo/%{app_id}.metainfo.xml

%changelog
* Thu Jun 04 2026 SwitchBros <switchbros@proton.me> - 1.1.2-1
- File logging, crash handler and scan diagnostics
- Open-log-folder menu entry
- Initial RPM package
