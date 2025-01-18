const form = document.querySelector("form");

form.addEventListener("submit", async function (event) {
    event.preventDefault(); 
    const formData = new FormData(form);
    try {
        console.log("b")
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            const data = await response.json();
            console.log(data);
            if (data.success) {
                window.location.href = data.newPath; 
            }else{
                window.location.reload()
                console.log("what the sigma??")
            }
        } else {
            console.error("Response not OK", response.status);
            window.location.reload()
        }
    } catch (error) {
        console.log(error)
    }
})