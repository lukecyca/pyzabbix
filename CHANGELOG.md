# Changelog

## [1.3.1](https://github.com/lukecyca/pyzabbix/compare/1.3.0...v1.3.1) (2023-12-18)


### Documentation

* add link to the zappix project ([#217](https://github.com/lukecyca/pyzabbix/issues/217)) ([962693d](https://github.com/lukecyca/pyzabbix/commit/962693d88a7cb3c53aeb0b7d62fc7198921abca8))
* regenerate changelog ([8747c18](https://github.com/lukecyca/pyzabbix/commit/8747c185503a74282df2b66d07ccb8f58a114d86))

<a name="1.3.0"></a>

## [1.3.0](https://github.com/lukecyca/pyzabbix/compare/1.2.1...1.3.0) (2023-04-08)

### :rocket: Features

- add zabbix 6.4 header authentication

<a name="1.2.1"></a>

## [1.2.1](https://github.com/lukecyca/pyzabbix/compare/1.2.0...1.2.1) (2022-08-25)

### :bug: Bug Fixes

- improve deprecation message for confimport

<a name="1.2.0"></a>

## [1.2.0](https://github.com/lukecyca/pyzabbix/compare/1.1.0...1.2.0) (2022-08-04)

### :bug: Bug Fixes

- catch ValueError during json parsing

### :rocket: Features

- parse version using packaging.version

<a name="1.1.0"></a>

## [1.1.0](https://github.com/lukecyca/pyzabbix/compare/1.0.0...1.1.0) (2022-07-28)

### :bug: Bug Fixes

- api object/method attributes should be private
- auto correct server url trailing slash

### :rocket: Features

- replace custom handler with logging.NullHandler
- package is typed
- deprecate ZabbixAPI.confimport alias
- allow creating calls using dict syntax
- replace dynamic func with ZabbixAPIMethod
- rename ZabbixAPIObjectClass to ZabbixAPIObject
- require >=python3.6

### Reverts

- chore: add more typings
