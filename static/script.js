Telegram.WebApp.ready();

Telegram.WebApp.MainButton.setText('Создать заказ').show().onClick(() => {
    const form = document.getElementById('orderForm');
    const description = document.getElementById('description').value;
    const category = document.getElementById('category').value;
    const city = document.getElementById('city').value;
    const price = document.getElementById('price').value;
    const deadline = document.getElementById('deadline').value;

    if (!description || !category || !city || !price || !deadline) {
        document.getElementById('message').innerText = 'Заполните все поля!';
        return;
    }

    const data = {
        telegram_id: Telegram.WebApp.initDataUnsafe.user.id,
        description,
        category,
        city,
        price,
        deadline
    };

    fetch('/create_order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            document.getElementById('message').innerText = result.error;
        } else {
            document.getElementById('message').innerText = `Заказ #${result.order_id} создан!`;
            form.reset();
        }
    })
    .catch(error => {
        document.getElementById('message').innerText = 'Ошибка: ' + error.message;
    });
});