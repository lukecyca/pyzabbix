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
