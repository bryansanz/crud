document.addEventListener("DOMContentLoaded", () => {
    // 1. Efecto magnético y de rebote sutil en botones de exportación
    const botonesAnimados = document.querySelectorAll('.btn-animate');

    botonesAnimados.forEach(boton => {
        boton.addEventListener('mouseenter', () => {
            boton.classList.add('animate__animated', 'animate__pulse');
            boton.style.transform = "scale(1.05) translateY(-2px)";
            boton.style.transition = "all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275)";
        });

        boton.addEventListener('mouseleave', () => {
            boton.classList.remove('animate__animated', 'animate__pulse');
            boton.style.transform = "scale(1) translateY(0px)";
        });
    });

    // 2. Animación de "Onda Líquida" al hacer click en el botón de registrar caso
    const btnSubmit = document.querySelector('.btn-submit');
    if (btnSubmit) {
        btnSubmit.addEventListener('click', (e) => {
            btnSubmit.classList.add('animate__animated', 'animate__rubberBand');
            
            // Creamos un efecto de ripple (onda) manual en CSS interno
            let x = e.clientX - e.target.offsetLeft;
            let y = e.clientY - e.target.offsetTop;
            
            let ripple = document.createElement('span');
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple-effect');
            
            btnSubmit.appendChild(ripple);
            setTimeout(() => { ripple.remove(); }, 600);
        });
        
        btnSubmit.addEventListener('animationend', () => {
            btnSubmit.classList.remove('animate__animated', 'animate__rubberBand');
        });
    }
});