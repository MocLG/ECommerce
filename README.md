🚀 Django Stripe Checkout IntegrationThis project implements a secure e-commerce payment solution using the Django framework for the backend and Stripe Checkout for handling secure transactions.The payment flow is secured using Stripe's Webhook system to ensure order status updates are reliable and cannot be spoofed by the client.
🌟 Key FeaturesDjango Backend: Robust, Python-based web framework.Stripe Checkout: Redirects customers to a secure, mobile-optimized payment page hosted by Stripe.Secure Webhooks: Critical component utilizing the Stripe Webhook API to confirm payment success and prevent client-side fraud.Modular Architecture: Uses dedicated apps: orders for transactions and pages for site content.
⚙️ Project StructureFile/DirectoryAppPurposemanage.pyRootDjango command-line utility..envRootStores all sensitive API keys and secrets. Must be in .gitignore.orders/models.pyordersDefines the Order model for database tracking.orders/views.pyordersContains the create_checkout_session (API call) and stripe_webhook_view (security endpoint).templates/orders/checkout.htmlordersThe HTML page containing the "Buy" button and the Stripe JavaScript trigger.templates/pages/home.htmlpagesThe site's main landing page.
🛠️ Setup and Installation1. Environment SetupBash# Navigate to the project root

# Create and activate a Python virtual environment
python -m venv venv
source venv/bin/activate 

# Install required Python packages
pip install django stripe python-dotenv
2. Stripe API Key ConfigurationRetrieve Keys: Get your Test API Keys (Publishable and Secret) from the Stripe Dashboard.Create .env File: In the project root (ecommerce_site/), create a file named .env and populate it:Code snippet# .env
STRIPE_PUBLISHABLE_KEY=pk_test_************************
STRIPE_SECRET_KEY=sk_test_****************************
STRIPE_WEBHOOK_SECRET=whsec_temp_cli_secret # REPLACE THIS TEMPORARILY DURING TESTING
Run Database Setup:Bashpython manage.py makemigrations 
python manage.py migrate
🧪 Local Webhook TestingTo securely test the payment confirmation and fulfillment flow, you must use the Stripe CLI to forward real-time webhook events to your local machine.1. Start Django ServerOpen your first terminal and ensure the server is running:Bashsource venv/bin/activate
python manage.py runserver
2. Start Stripe CLI ListenerOpen a second terminal and log in to your Stripe account:Bashstripe login
Then, start listening and forwarding events to your webhook URL:Bash# This command listens for the critical 'checkout.session.completed' event
stripe listen --forward-to localhost:8000/payment/stripe-webhook/
3. Run a Test TransactionAccess your local server (e.g., http://127.0.0.1:8000/).CRITICAL: Copy the temporary whsec_... key provided by the CLI and update the STRIPE_WEBHOOK_SECRET in your .env file.Navigate to your checkout page (checkout.html).Click the Buy Button and be redirected to Stripe Checkout.Use one of Stripe's Test Card Numbers to complete the purchase.The Stripe CLI terminal should show the event arriving, confirming that your webhook handler is working and the order status is securely updated in your database
