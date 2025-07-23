# Lectern snapshot

## Data pack

`@data_pack pack.mcmeta`

```json
{
  "pack": {
    "pack_format": 81,
    "description": ""
  }
}
```

### demo

`@function demo:foo`

```mcfunction
function demo:foo
function demo:foo/thing
function demo:thing
execute if function demo:foo/condition run function demo:foo/action
```

`@function demo:bar/thing`

```mcfunction
function #demo:bar/thing/aaa
```

`@function demo:wat/thing`

```mcfunction
function #demo:wat/thing/bbb
```

`@function demo:foo/this/thing`

```mcfunction
function #demo:foo/this/thing/ccc
```

`@function demo:upthis/thing`

```mcfunction
function #demo:upthis/thing/ddd
```

`@function demo:bar`

```mcfunction
function demo:bar
function demo:bar/thing
function demo:thing
```

`@function demo:wat`

```mcfunction
function demo:wat
function demo:wat/thing
function demo:thing
```

`@function demo:foo/this`

```mcfunction
function demo:foo/this
function demo:foo/this/thing
function demo:foo/thing
```

`@function demo:upthis`

```mcfunction
function demo:upthis
function demo:upthis/thing
function demo:thing
```
