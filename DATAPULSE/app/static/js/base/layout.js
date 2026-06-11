function toggleSidebar(){
    document.body.classList.toggle("sidebar-collapsed");

    localStorage.setItem(
        "sidebar",
        document.body.classList.contains("sidebar-collapsed")
    );
}

/* RESTORE ESTADO */
document.addEventListener("DOMContentLoaded", () => {
    if(localStorage.getItem("sidebar") === "true"){
        document.body.classList.add("sidebar-collapsed");
    }
});