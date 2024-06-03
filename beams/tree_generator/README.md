# Tree Generator
Contained is mechanisms to:
1. Parse and write to config files that specify tree structure
2. Generate tree objects to be ticked from file contents above

### TreeSerializer
Uses `apischema` to define file structure of config file and parse contents. 
TODO: make resilient to poorly formatted files. hash config file to get some form of version control

### TreeGenerator
Pass a node type and a file path for the config document and it will generate a tree 