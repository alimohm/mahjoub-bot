def generate_royal_invoice(order_data):
    # هنا نصمم الفاتورة بـ HTML ليكون التنسيق 100% مرتب
    html_content = f"""
    <div style="border: 2px solid #4b0082; padding: 20px; font-family: Arial;">
        <h1 style="color: #4b0082; text-align: center;">MAHJOUB ONLINE</h1>
        <hr>
        <p>رقم الطلب: {order_data['handel']}</p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #4b0082; color: white;">
                <th>المنتج</th>
                <th>الكمية</th>
                <th>السعر</th>
            </tr>
            {"".join([f"<tr><td>{item['title']}</td><td>{item['quantity']}</td><td>{item['price']}</td></tr>" for item in order_data['items']])}
        </table>
        <h3 style="text-align: left;">الإجمالي: {order_data['priceWithShipping']} ريال</h3>
    </div>
    """
    return html_content
