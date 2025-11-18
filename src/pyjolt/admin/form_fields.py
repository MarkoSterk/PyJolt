"""
A collection of form fields for admin dashboard forms.
"""
from datetime import datetime

class SelectField:
    """
    A form field representing a dropdown select input.
    """
    def __init__(self, choices: list[tuple[str|int|float, str]],
                 default: str|int|float| None = None, classes: list[str]|None = None,
                 required: bool = False):
        self.choices = choices
        self.default = default
        self.classes = classes or ["form-select"]
        self.required = required
    
    def __call__(self, id: str) -> str:
        return f"""
            <select class="{' '.join(self.classes)}" id="{id}" name="{id}" {"required" if self.required else ""}>
                {''.join(f'<option value="{value}" {"selected" if value == self.default else ""}>{label}</option>' for value, label in self.choices)}
            </select>
        """

class DatePickerField:
    """
    A form field representing a date picker input.
    """
    def __init__(self, default: str|datetime|None = None,
                 classes: list[str]|None = None, required: bool = False):
        self.default = default if isinstance(default, str) else (default.strftime("%Y-%m-%d") if default else None)
        self.classes = classes or ["form-control"]
        self.required = required
    
    def __call__(self, id: str) -> str:
        return f"""
            <input {"required" if self.required else ""} type="date" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default or ''}">
        """

class DateTimePickerField:
    """
    A form field representing a datetime picker input.
    """
    def __init__(self, default: str|datetime|None = None,
                 classes: list[str]|None = None, required: bool = False):
        self.default = default if isinstance(default, str) else (default.strftime("%Y-%m-%dT%H:%M") if default else None)
        self.classes = classes or ["form-control"]
        self.required = required
    
    def __call__(self, id: str) -> str:
        return f"""
            <input {"required" if self.required else ""} type="datetime-local" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default or ''}">
        """
    
class TextAreaField:
    """
    A form field representing a textarea input.
    """
    def __init__(self, rows: int = 5, default: str|None = None,
                 classes: list[str]|None = None, required: bool = False):
        self.rows = rows
        self.default = default or ""
        self.classes = classes or ["form-control"]
        self.required = required
    
    def __call__(self, id: str) -> str:
        return f"""
            <textarea {"required" if self.required else ""} class="{' '.join(self.classes)}" id="{id}" name="{id}" rows="{self.rows}">{self.default}</textarea>
        """

class CheckboxField:
    """
    A form field representing a checkbox input.
    """
    def __init__(self, checked: bool = False,
                 classes: list[str]|None = None,
                 required: bool = False):
        self.checked = checked
        self.classes = classes or ["form-check-input"]
        self.required = required
    
    def __call__(self, id: str) -> str:
        return f"""
            <input {"required" if self.required else ""} type="checkbox" class="{' '.join(self.classes)}" id="{id}" name="{id}" {"checked" if self.checked else ""}>
        """

class TextInputField:
    """
    A form field representing a text input.
    """
    def __init__(self, default: str|None = None,
                 classes: list[str]|None = None,
                 required: bool = False):
        self.default = default or ""
        self.classes = classes or ["form-control"]
        self.required = required
    
    def __call__(self, id: str) -> str:
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
                 step: int|float|None = None, required: bool = False):
        self.default = default if default is not None else ""
        self.classes = classes or ["form-control"]
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.required = required
    
    def __call__(self, id: str) -> str:
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
                 required: bool = False):
        self.default = default or ""
        self.classes = classes or ["form-control"]
        self.required = required
    
    def __call__(self, id: str) -> str:
        return f"""
            <input {"required" if self.required else ""} type="email" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """

class PasswordInputField:
    """
    A form field representing a password input.
    """
    def __init__(self, default: str|None = None,
                 classes: list[str]|None = None,
                 required: bool = False):
        self.default = default or ""
        self.classes = classes or ["form-control"]
        self.required = required
    
    def __call__(self, id: str) -> str:
        return f"""
            <input {"required" if self.required else ""} type="password" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """

class URLInputField:
    """
    A form field representing a URL input.
    """
    def __init__(self, default: str|None = None, classes: list[str]|None = None,
                 required: bool = False):
        self.default = default or ""
        self.classes = classes or ["form-control"]
        self.required = required
    
    def __call__(self, id: str) -> str:
        return f"""
            <input {"required" if self.required else ""} type="url" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """