/**
 * File explorer
 */

class FileExplorer extends HTMLElement{

    constructor(){
        super();
    }

    async connectedCallback(){
        this.ctrlDown = false;
        this.insertAdjacentHTML("afterbegin", this.markup());
        this.activate();
        await this.getFiles();
    }

    async getFiles(){
        let response = await fetch(`${this.baseFilesUrl}?path=${this.currentFolder}`);
        if(!response.ok){
            this.filesContainer.innerHTML = this.errorMarkup();
            return;
        }
        response = await response.json()
        this.files = response.data;
    }

    async rerender(){
        this.innerHTML = "";
        this.insertAdjacentHTML("afterbegin", this.markup());
        this.activate();
        await this.getFiles();
    }

    activate(){

        this.addEventListener("file-name-change", (e) => {
            this.allFiles.forEach((el) => {
                el.classList.remove("border");
            });
            this.deleteBtn.disabled = true;
            this.downloadAllBtn.disabled = true;
        })

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

        this.addEventListener("mousedown", (e) => {
            if(e.target.closest("file-element")){
                if(!this.ctrlDown){
                    this.allFiles.forEach((el) => {
                        el.classList.remove("border");
                    })
                }
                e.target.closest("file-element").classList.add("border");
                return;
            }
            if(!e.target.closest("file-element") && !this.ctrlDown){
                this.allFiles.forEach((el) => {
                    if(el.classList.contains("border")){
                        el.classList.remove("border");
                    }
                })
            }
        })

        this.addEventListener("mouseup", (e) => {
            const clickedFiles = Array.from(this.allFiles).filter((el) => {
                return el.classList.contains("border")
            });
            this.deleteBtn.disabled = !clickedFiles.length > 0;
            this.downloadAllBtn.disabled = !clickedFiles.length > 0;
        })
        this.deleteBtn.addEventListener("click", async (e) => {
            console.log("Deleting files...")
        })

        this.downloadAllBtn.addEventListener("click", async (e) => {
            console.log("Downloading files...")
        })

        this.pathLinks.forEach((link) => {
            link.addEventListener("click", (e) => {
                this.currentFolder = link.getAttribute("data-path");
            })
        })
    }

    noFilesMarkup(){
        return `
            <div class="text-center m-2">No files or folders...</div>
        `
    }

    errorMarkup(){
        return `
            <div class="text-center text-danger m-2">Something went wrong...</div>
        `
    }

    fileMarkup(file){
        return `
            <file-element data-is-folder="${file.is_folder}" data-file-name="${file.name}" data-file-path="${file.path}"></file-element>
        `
    }

    pathLinksParts(parts){
        let current = "";
        return parts.map(part => {
            current += `/${part}`;
            return current;
        });
    }

    pathLinksMarkup(parts, paths){
        let markup = "";
        paths.forEach((path, i) => {
            markup+=`<span class="path-link text-muted" role="button" data-path="${path}">${"/"+parts[i]}</span>`
        })
        return markup;
    }

    markup(){
        let parts = this.currentFolder;
        if(parts.startsWith("/")){
            parts = parts.substring(1);
        }
        parts = parts.split("/")
        return `
        <main class="card" aria-label="File explorer">
            <div class="card-header">
                <h2 class="title mb-0">File explorer</h2>
                <p class="text-muted">${this.pathLinksMarkup(parts, this.pathLinksParts(parts))}</p>
            </div>

            <div class="card-body">
                <div class="p-1">
                    <button type="button" class="btn btn-sm btn-secondary delete-btn" title="Delete files" disabled>
                        Delete <i class="fa-solid fa-trash"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-primary download-all-btn" title="Download all files" disabled>
                        Download <i class="fa-solid fa-download"></i>
                    </button>
                </div>
                <div class="d-flex flex-wrap gap-4 p-2 files-container">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            </div>
        </main>`
    }

    get currentFolder(){
        return this.getAttribute("data-current-folder");
    }

    set currentFolder(folder_path){
        this.setAttribute("data-current-folder", folder_path);
        this.rerender();
    }

    get baseFilesUrl(){
        return this.getAttribute("data-base-files-url");
    }

    get fetchFileUrl(){
        return this.getAttribute("data-base-single-file-url");
    }

    get renameUrl(){
        return this.getAttribute("data-rename-url");
    }

    get pathLinks(){
        return this.querySelectorAll(".path-link");
    }

    get allFiles(){
        return this.querySelectorAll("file-element");
    }

    get deleteBtn(){
        return this.querySelector(".delete-btn");
    }

    get downloadAllBtn(){
        return this.querySelector(".download-all-btn");
    }

    get filesContainer(){
        return this.querySelector(".files-container");
    }

    set files(files){
        if(files.length == 0){
            this.filesContainer.innerHTML = this.noFilesMarkup();
            return;
        }
        this.filesContainer.innerHTML = files.map(file => {return this.fileMarkup(file)}).join("");
    }

    get files(){
        return Array.from(this.allFiles).map((file) => {
            return {
                isFolder: file.isFolder,
                name: file.name,
                path: file.path
            }
        })
    }


}

export default FileExplorer;
