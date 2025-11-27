"""JavaScript snippets for admin dashboard"""

MESSAGES_SCRIPT: str = """
    <script>
        function removeMsg(id){
            const msg = document.getElementById(id)
            if(!msg){
                return;
            }
            msg.remove();
        }

        function generateMsg(msg, status, id){
            return `
                <div class="bg-${status} p-2 text-center w-100 mb-2" id="${id}">${msg}</div>
            `
        }
    
        function setMessage(msg, status){
            const msgContainer = document.querySelector('.messages');
            const msgId = 'msg-' + Math.floor(Math.random() * 1000);
            msgContainer.insertAdjacentHTML('beforeend', generateMsg(msg, status, msgId));
            setTimeout(() => {
                removeMsg(msgId);
            }, 6000)
        }
    </script>
"""

LOGOUT_SCRIPT: str = """
    <script>
        const btn = document.querySelector(".logout")
        btn.addEventListener('click', async (event) => {
            const logoutUrl = btn.getAttribute('data-logout-url');
            const loginUrl = btn.getAttribute('data-login-url');
            let response = await fetch(logoutUrl);
            if(response.ok){
                window.location.href= loginUrl;
                return;
            }
            return setMessage("Failed to logout from dashboard", "danger")
        })
    </script>
"""
