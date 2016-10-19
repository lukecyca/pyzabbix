#
# spec file for package python-docopt
#
# Copyright (c) 2016 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           python-pyzabbix
Version:        0.7.4
Release:        1
Url:            http://github.com/lukecyca/pyzabbix
Summary:        Zabbix API Python interface
License:        LGPL
Group:          Development/Languages/Python
Source:         https://github.com/lukecyca/pyzabbix/archive/%{version}.tar.gz
BuildRequires:  python-setuptools
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch
Requires:       python-requests >= 1.0

%description
PyZabbix is a Python module for working with the Zabbix API.

Tested against Zabbix 1.8 through 3.0.

%prep
%setup -q -n pyzabbix-%{version}

%build
python setup.py build

%install
python setup.py install --prefix=%{_prefix} --root=%{buildroot}

%files
%defattr(-,root,root,-)
%doc README.markdown
%{python_sitelib}

%changelog
* Tue Oct 19 2016 Benoit Mortier <benoit.mortier@opensides.be> - 0.7.4-1
- First release
