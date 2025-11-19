"""
A collection of form fields for admin dashboard forms.
"""
from datetime import datetime

def snake_to_kebab(value: str) -> str:
    """Convert a snake_case string to kebab-case."""
    return value.replace('_', '-')

class SelectField:
    """
    A form field representing a dropdown select input.
    """
    def __init__(self, options: list[tuple[str|int|float, str]],
                 default: str|int|float| None = None, classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.options = options
        self.default = default
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <select class="{' '.join(self.classes)}" id="{id}" name="{id}" {"required" if self.required else ""}>
                {''.join(f'<option value="{value}" {"selected" if value == self.default else ""}>{label}</option>' for value, label in self.options)}
            </select>
        """

class DatePickerField:
    """
    A form field representing a date picker input.
    """
    def __init__(self, default: str|datetime|None = None,
                 classes: list[str]|None = None, required: bool = False, **kwargs):
        self.default = default if isinstance(default, str) else (default.strftime("%Y-%m-%d") if default else None)
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <input {"required" if self.required else ""} type="date" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default or ''}">
        """

class DateTimePickerField:
    """
    A form field representing a datetime picker input.
    """
    def __init__(self, default: str|datetime|None = None,
                 classes: list[str]|None = None, required: bool = False, **kwargs):
        self.default = default if isinstance(default, str) else (default.strftime("%Y-%m-%dT%H:%M") if default else None)
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <input {"required" if self.required else ""} type="datetime-local" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default or ''}">
        """
    
class TextAreaField:
    """
    A form field representing a textarea input.
    """
    def __init__(self, rows: int = 5, default: str|None = None,
                 classes: list[str]|None = None, required: bool = False, **kwargs):
        self.rows = rows
        self.default = default or ""
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <textarea {"required" if self.required else ""} class="{' '.join(self.classes)}" id="{id}" name="{id}" rows="{self.rows}">{self.default}</textarea>
        """

class CheckboxField:
    """
    A form field representing a checkbox input.
    """
    def __init__(self, checked: bool = False,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.checked = checked
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <input {"required" if self.required else ""} type="checkbox" class="{' '.join(self.classes)}" id="{id}" name="{id}" {"checked" if self.checked else ""}>
        """

class TextInputField:
    """
    A form field representing a text input.
    """
    def __init__(self, default: str|None = None,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or ""
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <input {"required" if self.required else ""} type="text" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """

class NumberInputField:
    """
    A form field representing a number input.
    """
    def __init__(self, default: int|float|None = None,
                 classes: list[str]|None = None,
                 min_value: int|float|None = None, max_value: int|float|None = None,
                 step: int|float|None = None, required: bool = False, **kwargs):
        self.default = default if default is not None else ""
        self.classes = classes or []
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <input {"required" if self.required else ""} type="number" class="{' '.join(self.classes)}" id="{id}" name="{id}"
                   value="{self.default}"
                   {'min="'+str(self.min_value)+'"' if self.min_value is not None else ''}
                   {'max="'+str(self.max_value)+'"' if self.max_value is not None else ''}
                   {'step="'+str(self.step)+'"' if self.step is not None else ''}>
        """

class EmailInputField:
    """
    A form field representing an email input.
    """
    def __init__(self, default: str|None = None,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or ""
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <input {"required" if self.required else ""} type="email" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """

class PasswordInputField:
    """
    A form field representing a password input.
    """
    def __init__(self, default: str|None = None,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or ""
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <input {"required" if self.required else ""} type="password" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """

class URLInputField:
    """
    A form field representing a URL input.
    """
    def __init__(self, default: str|None = None, classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or ""
        self.classes = classes or []
        self.required = required
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        return f"""
            <input {"required" if self.required else ""} type="url" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """
    
class TagsInput:
    """
    A form field representing a tags input.
    """
    def __init__(self, *, default: list[str]|None = None,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or []
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None) -> str:
        if classes is not None:
            self.classes.extend(classes)
        default_tags = ",".join(self.default)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <tags-input {kwargs_str} {"required" if self.required else ""} class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{default_tags}"></tags-input>
        """
