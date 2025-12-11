/**
 * FileElement for file explorer
 */


class FileElement extends HTMLElement {

    constructor() {
        super();
        this._value = [];
    }

    connectedCallback() {
        this.ctrlDown = false;
        this.innerHTML = this.markup();
        this.activate();
    }

    markup(){
        return `
            <div class="d-flex flex-column align-items-center text-center p-1"
                    style="width: 120px;" role="button" tabindex="0">
                <div hidden class="file-actions">
                </div>
                <div class="mb-1">
                    ${this.isFolder ? '<i class="fa-regular fa-folder fa-4x"></i>' : '<i class="fa-solid fa-file fa-4x"></i>'}
                </div>
                <div class="text-truncate w-100 name-container" title="${this.name}">
                    ${this.name}
                </div>
            </div>
        `
    }

    activate(){

        document.addEventListener("keydown", (e) => {
            if(["Control"].includes(e.key)){
                this.ctrlDown = true;
            }
        })

        document.addEventListener("keyup", (e) => {
            if(["Control"].includes(e.key)){
                this.ctrlDown = false;
            }
        })

        document.addEventListener("mousedown", (e) => {
            if(e.target.closest("file-element") !== this && !this.ctrlDown){
                this.container.classList.remove("border");
            }
        })

        this.container.addEventListener("click", (e) => {
            this.container.focus()
        })

        this.container.addEventListener("focus", (e) => {
            this.container.classList.add("border");
        })

        this.container.addEventListener("focusout", (e) => {
            if(this.ctrlDown){
                e.preventDefault();
                return;
            }
            this.container.classList.remove("border");
        })

        this.container.addEventListener("dblclick", (e) => {
            if(this.isFolder){
                this.handleFolderDblClick(e);
            }else{
                this.handleFileDblClick(e);
            }
        });

        this.nameContainer.addEventListener("dblclick", (e) => {
            this.handleNameContainerDblClick(e);
        })

        this.nameContainer.addEventListener("focusout", async (e) => {
            this.nameContainer.removeAttribute("contenteditable");
            const nameChanged = this.name != this.nameContainer.innerHTML.trim();
            if(!nameChanged){
                return;
            }
            this.setAttribute("data-file-name", this.nameContainer.innerHTML.trim());
            await changeFileName(e);
        });
    }

    /**
     * 
     * @param {Event} e 
     */
    handleFolderDblClick(e){
        console.log("Double click...Opening folder")
    }

    /**
     * 
     * @param {Event} e 
     */
    handleFileDblClick(e){
        console.log("Double click...Opening file...")
    }

    /**
     * 
     * @param {Event} e 
     */
    handleNameContainerDblClick(e){
        e.preventDefault();
        e.stopPropagation();
        this.nameContainer.setAttribute("contenteditable", "true");
        this.nameContainer.innerHTML = this.nameContainer.innerHTML.trim();
        this.nameContainer.focus();
    }

    async changeFileName(e){
        console.log("Changing file name...")
    }

    get isFolder(){
        return ["True", true, "true", "data-is-folder", "is-folder", 1, "1"].includes(this.getAttribute("data-is-folder"))
    }

    get name(){
        return this.getAttribute("data-file-name")
    }

    get path(){
        return this.getAttribute("data-file-path")
    }

    get container(){
        return this.querySelector('div[role="button"]')
    }

    get nameContainer(){
        return this.querySelector(".name-container");
    }
    
}

export default FileElement;