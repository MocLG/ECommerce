# 🛒 Django E-Commerce with Stripe Checkout

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.1+-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A secure, full-featured e-commerce application built with Django and Stripe Checkout integration. This project implements a complete online shopping experience with product browsing, shopping cart functionality, user authentication, and secure payment processing.

## ✨ Features

### Core Functionality
- **Product Catalog**: Browse and search products with detailed information
- **Shopping Cart**: Add, remove, and manage items in your cart
- **User Authentication**: Secure user registration, login, and profile management
- **Order Management**: Track order history and status
- **Stripe Checkout**: Secure payment processing with Stripe's hosted checkout page
- **Webhook Integration**: Reliable order confirmation using Stripe webhooks
- **Admin Dashboard**: Manage products, orders, and users through Django admin

### Security Features
- Secure webhook validation to prevent payment fraud
- CSRF protection on all forms
- Environment-based configuration for sensitive data
- Secure session management

## 🏗️ Project Structure

```
ECommerce/
├── accounts/           # User authentication and profile management
├── cart/              # Shopping cart functionality
├── core/              # Project settings and configuration
├── orders/            # Order processing and Stripe integration
├── shop/              # Product catalog and shop functionality
├── templates/         # HTML templates
├── manage.py          # Django management script
├── requirements.txt   # Python dependencies
└── .env              # Environment variables (not in repo)
```

### Key Files

| File/Directory | Purpose |
|----------------|---------|
| `manage.py` | Django command-line utility |
| `.env` | Stores sensitive API keys and secrets (must be in `.gitignore`) |
| `orders/models.py` | Order model for database tracking |
| `orders/views.py` | Stripe checkout and webhook endpoints |
| `shop/models.py` | Product and category models |
| `cart/cart.py` | Shopping cart session management |

## 🚀 Setup and Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Stripe account (for payment processing)
- PostgreSQL (for production) or SQLite (for development)

### 1. Clone the Repository

```bash
git clone https://github.com/MocLG/ECommerce.git
cd ECommerce
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Stripe API Keys (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_PUBLISHABLE_KEY=pk_test_************************
STRIPE_SECRET_KEY=sk_test_****************************
STRIPE_WEBHOOK_SECRET=whsec_*************************

# Database (optional for production)
DATABASE_URL=postgresql://user:password@localhost/dbname
```

> **Note**: Never commit your `.env` file to version control!

### 5. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## 🧪 Testing Stripe Integration

To test payments locally, you'll need to set up webhook forwarding using the Stripe CLI.

### 1. Install Stripe CLI

Follow the [Stripe CLI installation guide](https://stripe.com/docs/stripe-cli#install).

### 2. Start Django Server

In your first terminal:

```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py runserver
```

### 3. Start Stripe Webhook Listener

In a second terminal:

```bash
# Login to Stripe
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:8000/payment/stripe-webhook/
```

Copy the webhook signing secret (`whsec_...`) displayed by the CLI and update `STRIPE_WEBHOOK_SECRET` in your `.env` file.

### 4. Test a Payment

1. Navigate to `http://127.0.0.1:8000/`
2. Add items to your cart
3. Proceed to checkout
4. Use [Stripe test card numbers](https://stripe.com/docs/testing):
   - **Success**: `4242 4242 4242 4242`
   - **Decline**: `4000 0000 0000 0002`
   - Use any future expiration date and any CVC

The webhook listener will show the event being received and processed.

## 📦 Deployment

This application is ready for deployment on platforms like:

- **Heroku**: Use the included `Procfile` and `runtime.txt`
- **Railway**: Direct deployment from GitHub
- **DigitalOcean App Platform**: Configure from the dashboard
- **AWS/Google Cloud**: Deploy using your preferred method

### Deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Configure static file serving (WhiteNoise or CDN)
- [ ] Set production webhook secret from Stripe Dashboard
- [ ] Enable HTTPS
- [ ] Set up environment variables on your platform

## 🔧 Development

### Project Apps

- **accounts**: User registration, authentication, and profiles
- **shop**: Product catalog, categories, and product details
- **cart**: Shopping cart session management
- **orders**: Order creation and Stripe payment processing

### Admin Access

Access the Django admin at `http://127.0.0.1:8000/admin/` to manage:
- Products and categories
- Orders and order items
- Users and permissions

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework used
- [Stripe](https://stripe.com/) - Payment processing
- [Bootstrap](https://getbootstrap.com/) - Frontend framework

## 📞 Support

If you have any questions or run into issues, please open an issue on GitHub.

---

Made with ❤️ by MocLG
