"""
WTForm inputs
"""
from __future__ import annotations
from enum import StrEnum
import typing
from typing import Type, cast, NewType, Any, Union, get_args, get_origin, get_type_hints
from abc import ABC, abstractmethod
from markupsafe import Markup
from wtforms.widgets import html_params
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped

from ..database.sql.declarative_base import DeclarativeBaseModel
from ..utilities import to_kebab_case

class FormFieldTypes(StrEnum):
    TAGS = "TagsField"
    PASSWORD = "PasswordField"
    EMAIL = "EmailField"
    TEXT = "TextField"
    TEXTAREA = "TextAreaField"
    SELECT = "SelectField"
    RADIO = "RedioField"
    CHECKBOX = "CheckboxField"

class FormField(ABC):

    type: FormFieldTypes = cast(FormFieldTypes, None)

    def __init__(self, **kwargs):
        """
        Initilizer for HTML input elements. Accepts any number of keyword arguments. Each argument will be treated as 
        a html attribute.
        """
        if self.type is None:
            raise NotImplementedError("FormField type must be defined in subclass with a defined type attribute of type FormFieldTypes.")
        self.id = kwargs.pop("id", None)
        self.name = kwargs.pop("name", None)
        self._label = kwargs.pop("label", None)
        self.kwargs = kwargs

        if self.id is None or self.name is None:
            raise Exception("FormField element must have a valid id and name parameter.")

    def __call__(self, **kwargs):
        """
        Render: <tags-input ...standard attrs... as-string="..."></tags-input>
        """
        kwargs.pop("id", None)
        kwargs.pop("name", None)
        kwargs.pop("label", None)
        self.kwargs.update(kwargs)

        for attr, value in self.kwargs.items():
            attr = to_kebab_case(attr)
            kwargs[attr] = value

        return self.markup(**kwargs)
    
    def generate_string_attributes(self, **kwargs) -> str:
        """Generates a string with html attributes corresponding to the kwargs object"""
        return html_params(**kwargs)
    
    @abstractmethod
    def markup(self, **kwargs) -> Markup:
        """Must return the markuo of the element"""
        pass
    
    def label(self, **kwargs) -> Markup:
        """
        Generates the label markup for the form field.
        """
        if self._label is None:
            return Markup("")

        return Markup(f'<label for="{self.id}" class="{kwargs.get('class', '')}" style="{kwargs.get('style', '')}">{self._label}</label>')

class TagsInput(FormField):

    type: FormFieldTypes = FormFieldTypes.TAGS

    def __init__(self, **kwargs):
        """
        Initlizer for TagsInput element. Accepts standard html attributes
        and the special boolean attribute: "as_string". 
        If as_string=True, the return value of the html element will be a comma separated string,
        otherwise it will be a list of strings.
        """
        super().__init__(**kwargs)

    def markup(self, **kwargs) -> Markup:
        attrs = self.generate_string_attributes(**kwargs)
        return Markup(f'<tags-input id="{self.id}" name="{self.name}" {attrs}></tags-input>')

class PasswordInput(FormField):
    """
    Password input field
    """

    type: FormFieldTypes = FormFieldTypes.PASSWORD

    def markup(self, **kwargs) -> Markup:
        """
        Password field input
        """
        attrs = self.generate_string_attributes(**kwargs)
        return Markup(f'<input type="password" id="{self.id}" name="{self.name}" {attrs} />')

class EmailInput(FormField):
    """
    Email input field
    """

    type: FormFieldTypes = FormFieldTypes.EMAIL

    def markup(self, **kwargs) -> Markup:
        """
        Email field input
        """
        attrs = self.generate_string_attributes(**kwargs)
        return Markup(f'<input type="email" id="{self.id}" name="{self.name}" {attrs} />')

class TextInput(FormField):
    """
    Text input field
    """

    type: FormFieldTypes = FormFieldTypes.TEXT

    def markup(self, **kwargs) -> Markup:
        """
        Text field input
        """
        attrs = self.generate_string_attributes(**kwargs)
        return Markup(f'<input type="text" id="{self.id}" name="{self.name}" {attrs} />')

class TextAreaInput(FormField):
    """
    Text input field
    """

    type: FormFieldTypes = FormFieldTypes.TEXTAREA

    def markup(self, **kwargs) -> Markup:
        """
        Textarea field input
        """
        attrs = self.generate_string_attributes(**kwargs)
        return Markup(f'<textarea type="text" id="{self.id}" name="{self.name}" {attrs}></textarea>')

class SelectInput(FormField):
    """
    Select input field
    """

    type: FormFieldTypes = FormFieldTypes.SELECT

    def __init__(self, **kwargs):
        options = kwargs.pop("options", None)
        super().__init__(**kwargs)
        self.options = options
        if self.options is None or not isinstance(self.options, list) or not isinstance(self.options[0], tuple):
            raise Exception("Please provide a list of tuples (value, name) as options")
    
    def generate_options(self) -> str:
        """Generates options string"""
        options: str = ""
        for val, name in self.options:
            options+=f'<option value="{val}">{name}</options>'
        return options

    def markup(self, **kwargs) -> Markup:
        """
        Select field input
        """
        attrs = self.generate_string_attributes(**kwargs)
        options: str = self.generate_options()
        return Markup(f'<select type="text" id="{self.id}" name="{self.name}" {attrs}>{options}</select>')

class CheckboxInput(FormField):
    """
    Checkbox input field
    """

    type: FormFieldTypes = FormFieldTypes.CHECKBOX

    def markup(self, **kwargs) -> Markup:
        """
        Checkbox field input
        """
        attrs = self.generate_string_attributes(**kwargs)
        return Markup(f'<input type="checkbox" id="{self.id}" name="{self.name}" {attrs} />')

class RadioInput(FormField):
    """
    Radio input field
    """

    type: FormFieldTypes = FormFieldTypes.RADIO

    def markup(self, **kwargs) -> Markup:
        """
        Radio field input
        """
        attrs = self.generate_string_attributes(**kwargs)
        return Markup(f'<input type="radio" id="{self.id}" name="{self.name}" {attrs} />')

EmailStr = NewType("EmailStr", str)
PasswordStr = NewType("PasswordStr", str)
TextStr = NewType("TextStr", str)
SelectStr = NewType("SelectStr", str)
CheckboxBool = NewType("CheckboxBool", bool)
RadioBool = NewType("RadioBool", bool)

TYPE_TO_FIELD = {
    ("list", str): TagsInput,
    PasswordStr: PasswordInput,
    EmailStr: EmailInput,
    TextStr: TextAreaInput,
    str: TextInput,
    SelectStr: SelectInput,
    CheckboxBool: CheckboxInput,
    RadioBool: RadioInput,
}

def _unwrap_optional(t: Any) -> tuple[Any, bool]:
    origin = get_origin(t)
    if origin is Union:
        args = list(get_args(t))
        if type(None) in args and len(args) == 2:
            args.remove(type(None))
            return args[0], False
    return t, True

def _unwrap_annotated(t: Any) -> Any:
    if get_origin(t) is getattr(typing, "Annotated", object()):
        return get_args(t)[0]
    return t

def _mapped_arg(ann: Any) -> Any | None:
    if get_origin(ann) is Mapped:
        return get_args(ann)[0]
    return None

def _resolve_newtype(t: Any) -> Any:
    return getattr(t, "__supertype__", t)

def _field_for_type(t: Any):
    """
    Resolve a python type (possibly NewType / Optional / list[str]) to an InputField
    using the module-level TYPE_TO_FIELD mapping.
    """
    if t in TYPE_TO_FIELD:
        return TYPE_TO_FIELD[t]

    t = _resolve_newtype(t)
    if t in TYPE_TO_FIELD:
        return TYPE_TO_FIELD[t]

    origin = get_origin(t)
    args = get_args(t)

    if origin is list and args == (str,):
        return TYPE_TO_FIELD.get(("list", str))

    for base in getattr(t, "__mro__", ()):
        if base in TYPE_TO_FIELD:
            return TYPE_TO_FIELD[base]

    return None


def build_fields(
    model_cls: Type[DeclarativeBaseModel],
    *,
    include_pk: bool = False,
    include_fk: bool = True,
) -> dict[str, Any]:
    """
    Builds {column_name: InputField} based on Mapped[T] annotations on model_cls.
    - Only includes real mapped columns (not relationships).
    - Can include/exclude PK and FK columns.
    """
    mapper = inspect(model_cls)

    column_props = {prop.key: prop for prop in mapper.column_attrs}
    table_cols_by_key = {col.key: col for col in mapper.local_table.columns}

    hints = get_type_hints(model_cls, include_extras=True)

    out: dict[str, Any] = {}

    for name, ann in hints.items():
        if name not in column_props:
            continue

        col = table_cols_by_key.get(name)
        if col is not None:
            if not include_pk and bool(getattr(col, "primary_key", False)):
                continue
            if not include_fk and bool(getattr(col, "foreign_keys", set())):
                continue

        mapped_t = _mapped_arg(ann)
        if mapped_t is None:
            continue

        mapped_t = _unwrap_annotated(mapped_t)
        base_t, required = _unwrap_optional(mapped_t)

        field_cls = _field_for_type(base_t)
        if field_cls is None:
            raise KeyError(f"No InputField mapping for {base_t!r} (column {name})")

        out[name] = field_cls(required=required) if callable(field_cls) else field_cls

    return out
