/**
 * Custom JS for admin dashboard
 */
import TagsInput from "./custom_js/tags_input.js";
import RecipientsInput from "./custom_js/email_recipients_input.js";
import FilesInput from "./custom_js/file_upload_input.js"
import FileElement from "./custom_js/file_explorer_file.js";
import FileExplorer from "./custom_js/file_explorer.js";

customElements.define("tags-input", TagsInput);
customElements.define("recipients-input", RecipientsInput);
customElements.define("files-input", FilesInput);
customElements.define("file-element", FileElement);
customElements.define("file-explorer", FileExplorer);
