/**
 * File explorer
 */

class FileExplorer extends HTMLElement{

    constructor(){
        super();
    }

    connectedCallback(){
        this.insertAdjacentHTML("afterbegin", this.markup());
    }

    activate(){
        this.addEventListener("mousedown", (e) => {
            console.log("click...")
            const clickedFiles = Array.from(this.allFiles).filter((el) => el.classList.contains("border"));
            this.deleteBtn.disabled = !clickedFiles.length > 0;
        })
    }

    markup(){
        return `<div class="p-1">
            <button type="button" class="btn btn-sm btn-secondary delete-btn" title="Delete files" disabled>
                Delete <i class="fa-solid fa-trash"></i>
            </button>
        </div>`
    }

    get allFiles(){
        return this.querySelectorAll("file-element");
    }

    get deleteBtn(){
        this.querySelector(".delete-btn");
    }


}

export default FileExplorer;
