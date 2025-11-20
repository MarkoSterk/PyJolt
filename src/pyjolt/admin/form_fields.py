"""
A collection of form fields for admin dashboard forms.
"""
from datetime import datetime
from enum import StrEnum

def snake_to_kebab(value: str) -> str:
    """Convert a snake_case string to kebab-case."""
    return value.replace('_', '-')

class FormFieldTypes(StrEnum):
    SELECT = "SelectField"
    DATE_PICKER = "DateField"
    DATETIME_PICKER = "DateTimeField"
    TEXT_AREA = "TextAreaField"
    CHECKBOX = "BooleanField"
    TEXT_INPUT = "StringField"
    NUMBER_INPUT = "IntegerField"
    EMAIL_INPUT = "EmailField"
    PASSWORD_INPUT = "PasswordField"
    URL_INPUT = "URLField"
    TAGS_INPUT = "TagsField"

class FormField:
    """
    Base class for form fields.
    """
    type: FormFieldTypes
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        raise NotImplementedError("FormField subclasses must implement the __call__ method.")
    
    def label(self, **kwargs) -> str:
        """Returns the label for the form field"""
        classes = kwargs.get("class", [])
        label = kwargs.get("label", getattr(self, "id", ""))
        return f'<label for="{getattr(self, 'id', '')}" class="{''.join(classes)}">{label}</label>'

class SelectField(FormField):
    """
    A form field representing a dropdown select input.
    """
    type = FormFieldTypes.SELECT
    def __init__(self, options: list[tuple[str|int|float, str]],
                 default: str|int|float| None = None, classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.options = options
        self.default = default
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <select {kwargs_str} class="{' '.join(self.classes)}" id="{id}" name="{id}" {"required" if self.required else ""}>
                {''.join(f'<option value="{value}" {"selected" if value == self.default else ""}>{label}</option>' for value, label in self.options)}
            </select>
        """

class DatePickerField(FormField):
    """
    A form field representing a date picker input.
    """
    type = FormFieldTypes.DATE_PICKER
    def __init__(self, default: str|datetime|None = None,
                 classes: list[str]|None = None, required: bool = False, **kwargs):
        self.default = default if isinstance(default, str) else (default.strftime("%Y-%m-%d") if default else None)
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <input {kwargs_str} {"required" if self.required else ""} type="date" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default or ''}">
        """

class DateTimePickerField(FormField):
    """
    A form field representing a datetime picker input.
    """
    type = FormFieldTypes.DATETIME_PICKER
    def __init__(self, default: str|datetime|None = None,
                 classes: list[str]|None = None, required: bool = False, **kwargs):
        self.default = default if isinstance(default, str) else (default.strftime("%Y-%m-%dT%H:%M") if default else None)
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <input {kwargs_str} {"required" if self.required else ""} type="datetime-local" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default or ''}">
        """
    
class TextAreaField(FormField):
    """
    A form field representing a textarea input.
    """
    type = FormFieldTypes.TEXT_AREA
    def __init__(self, rows: int = 5, default: str|None = None,
                 classes: list[str]|None = None, required: bool = False, **kwargs):
        self.rows = rows
        self.default = default or ""
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <textarea {kwargs_str} {"required" if self.required else ""} class="{' '.join(self.classes)}" id="{id}" name="{id}" rows="{self.rows}">{self.default}</textarea>
        """

class CheckboxField(FormField):
    """
    A form field representing a checkbox input.
    """
    type = FormFieldTypes.CHECKBOX
    def __init__(self, checked: bool = False,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.checked = checked
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <input {kwargs_str} {"required" if self.required else ""} type="checkbox" class="{' '.join(self.classes)}" id="{id}" name="{id}" {"checked" if self.checked else ""}>
        """

class TextInputField(FormField):
    """
    A form field representing a text input.
    """
    type = FormFieldTypes.TEXT_INPUT
    def __init__(self, default: str|None = None,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or ""
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <input {kwargs_str} {"required" if self.required else ""} type="text" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """

class NumberInputField(FormField):
    """
    A form field representing a number input.
    """
    type = FormFieldTypes.NUMBER_INPUT
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
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <input {kwargs_str} {"required" if self.required else ""} type="number" class="{' '.join(self.classes)}" id="{id}" name="{id}"
                   value="{self.default}"
                   {'min="'+str(self.min_value)+'"' if self.min_value is not None else ''}
                   {'max="'+str(self.max_value)+'"' if self.max_value is not None else ''}
                   {'step="'+str(self.step)+'"' if self.step is not None else ''}>
        """

class EmailInputField(FormField):
    """
    A form field representing an email input.
    """
    type = FormFieldTypes.EMAIL_INPUT
    def __init__(self, default: str|None = None,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or ""
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <input {kwargs_str} {"required" if self.required else ""} type="email" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """

class PasswordInputField(FormField):
    """
    A form field representing a password input.
    """
    type = FormFieldTypes.PASSWORD_INPUT
    def __init__(self, default: str|None = None,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or ""
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <input {kwargs_str} {"required" if self.required else ""} type="password" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """

class URLInputField(FormField):
    """
    A form field representing a URL input.
    """
    type = FormFieldTypes.URL_INPUT
    def __init__(self, default: str|None = None, classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or ""
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <input {kwargs_str} {"required" if self.required else ""} type="url" class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{self.default}">
        """
    
class TagsInput(FormField):
    """
    A form field representing a tags input.
    """
    type = FormFieldTypes.TAGS_INPUT
    def __init__(self, *, default: list[str]|None = None,
                 classes: list[str]|None = None,
                 required: bool = False, **kwargs):
        self.default = default or []
        self.classes = classes or []
        self.required = required
        self.kwargs = kwargs
    
    def __call__(self, id: str, classes: list[str]|None = None, **kwargs) -> str:
        if classes is not None:
            self.classes.extend(classes)
        if kwargs:
            self.kwargs.update(kwargs)
        default_tags = ",".join(self.default)
        kwargs_str = " ".join(f'{snake_to_kebab(key)}="{value}"' for key, value in self.kwargs.items())
        return f"""
            <tags-input {kwargs_str} {"required" if self.required else ""} class="{' '.join(self.classes)}" id="{id}" name="{id}" value="{default_tags}"></tags-input>
        """
