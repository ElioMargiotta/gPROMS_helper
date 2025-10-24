# Contributing to gPROMS Process Simulation Data Processing

Thank you for your interest in contributing to this project! This guide will help you get started with contributing to the gPROMS data processing toolkit.

## Getting Started

1. **Fork the repository** and clone your fork locally
2. **Set up your development environment** following the installation instructions in README.md
3. **Create a new branch** for your feature or bug fix:
   ```powershell
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Standards

When modifying or extending the codebase, please follow these guidelines:

1. **Preserve data precision** - always use scientific notation for numerical values
2. **Maintain hierarchy** - respect the equipment path structure 
3. **Handle missing data** - many variables may have empty units or bounds
4. **Test with real data** - use actual simulation files for validation
5. **Follow naming conventions** - use the established `Trials/` and `Corrections/` directory patterns

### Scientific Notation Handling

Always use the `format_scientific_notation()` function for numerical formatting:

```python
# Correct - maintains 16-digit precision
f"{num:.16e}"

# Avoid - loses precision
str(float_value)
```

### Path Processing

Respect the hierarchical equipment structure:

```python
# Correct - preserves equipment hierarchy
path_parts = path_name.split('.')
folder_path = os.path.join(output_base_dir, *path_parts[:-1])

# Variable name is always the last component
variable_name = path_parts[-1]
```

### Error Handling

Follow the established pattern for robust data processing:

```python
try:
    value = float(value_str)
    # Process value
except ValueError:
    print(f"Warning: Could not convert value '{value_str}' to float for path '{path_name}'")
    continue  # Skip malformed data but continue processing
```

## Testing

### Manual Testing

1. **Test with real gSTORE-4 files** from the `Trials/` directory
2. **Verify round-trip accuracy** - parse then reconstruct files should match original precision
3. **Check hierarchical organization** - ensure folder structures mirror equipment paths
4. **Validate CSV format** - ensure 6-column format is maintained

### Test Data

Use the existing test files in the repository:
- `Trials/run1/run_1.txt` - Standard test case
- `Trials/MEA_DEEA(1;1)/run_1.txt` - Special character handling

## Submitting Changes

### Pull Request Process

1. **Ensure your code follows the guidelines** above
2. **Test your changes** with existing simulation files
3. **Update documentation** if you've added new features
4. **Create a pull request** with:
   - Clear description of changes
   - Examples of usage (if applicable)
   - Test results with sample files

### Pull Request Template

```markdown
## Description
Brief description of changes and motivation

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Tested with existing simulation files
- [ ] Verified round-trip accuracy (parse → reconstruct)
- [ ] Checked hierarchical organization
- [ ] Validated scientific notation precision

## Files Changed
List of modified files and brief explanation of changes
```

## Areas for Contribution

### High Priority
- **Performance optimization** for large files (>50K variables)
- **Memory usage improvements** in processing pipeline
- **Additional analysis functions** for specific equipment types
- **Batch processing enhancements** for multiple runs

### Medium Priority
- **Error reporting improvements** with detailed line-by-line feedback
- **Configuration file support** for processing parameters
- **Data validation tools** for gSTORE-4 format compliance
- **Unit conversion utilities** for different measurement systems

### Documentation
- **Code examples** for specific use cases
- **Equipment-specific analysis guides** 
- **Performance benchmarking** documentation
- **Integration guides** with other gPROMS tools

## Code Review Guidelines

When reviewing contributions:

1. **Verify precision handling** - check that scientific notation is preserved
2. **Test hierarchical organization** - ensure equipment paths create correct folders
3. **Validate error handling** - confirm malformed data doesn't break processing
4. **Check file compatibility** - ensure changes work with existing simulation files
5. **Review performance impact** - consider memory and processing time effects

## Questions and Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and general discussion
- **Documentation**: Check the README.md and `.github/copilot-instructions.md` for project-specific guidance

## Recognition

Contributors will be acknowledged in the project documentation. Significant contributions may be recognized with maintainer access.

Thank you for helping improve the gPROMS data processing toolkit!