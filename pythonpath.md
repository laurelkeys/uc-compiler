# Working with interdependent files

## Option 1) Change `sys.path` on each module

```python
# at project-1/ files:
sys.path.insert(0, os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/../project-2"
))

# at project-2/ files:
sys.path.insert(0, os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/../project-1"
))
```

## Option 2) Set the `PYTHONPATH` environment variable through VS Code

```javascript
// on launch.json:
"configurations": [
    {
        "env": {
            "PYTHONPATH": "${workspaceFolder}/project-1;${workspaceFolder}/project-2"
        }
        // ...
    }
]

// on settings.json:
"python.autoComplete.extraPaths": [
    "./project-1",
    "./project-2",
],
// ...
```