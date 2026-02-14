## 🌉 Why Content Bridge?

Managing content across multiple social platforms is fragmented, time-consuming, and error-prone. Teams often juggle separate dashboards for Telegram, Bale, and other channels — leading to inconsistent messaging, missed scheduling opportunities, and duplicated effort.

**Content Bridge solves this** by providing a single, unified interface where you can:
- Compose once, publish everywhere
- Schedule posts with precision
- Reuse media assets across campaigns
- Track engagement with built-in analytics
- Enhance content strategy using AI suggestions

Built for digital teams, marketers, and community managers, Content Bridge streamlines your workflow while keeping security and scalability in mind.

## ⚙️ Technology Stack

Content Bridge is a modern, containerized application built with:

- **Frontend**: React + Vite (TypeScript-ready, no Tailwind — pure CSS)
- **Backend**: Django REST Framework (Python) with JWT authentication
- **AI Service**: FastAPI for lightweight, async AI inference
- **Database**: PostgreSQL (production-grade relational storage)
- **Caching & Messaging**: Redis (for Celery task queues and caching)
- **Task Processing**: Celery + Celery Beat (for scheduled posts and reports)
- **Infrastructure**: Docker & Docker Compose (7 isolated services)
- **Security**: HttpOnly cookies, CSRF protection disabled (dev-only), secure token policies
- **Integrations**: Telegram Bot API, Bale Bot API

The entire system runs locally via Docker Compose — ideal for development, testing, and future deployment.


Make sure you have the following installed:
Docker Desktop (v20+)
Git


### Environment Configuration

Inside the `Back-end` and `aiService` directories, you need to configure environment variables according to your setup.  
Detailed explanations are already provided as comments inside the `.env` files.

In summary, you will need:
- An email address with an **app-specific password**
- An **API token** and An **AI model name** obtained from **https://openrouter.ai/**


⚠️ **Security Note**  
For any usage beyond testing and evaluation, it is strongly recommended to define sensitive values such as `security_key`, database passwords, and other confidential data yourself, following standard security best practices.

---

### Build and Run with Docker
first clone repository :
```bash
git clone https://github.com/alirezarazani2003/content-bridge.git
cd content-bridge
```

then run:

```bash
docker-compose up --build -d
```
Wait until all services are fully built and started.

### Apply Database Migrations
After the containers are running, execute the following command:
```bash
docker-compose exec backend python manage.py migrate
```

### Create an Initial Superuser
Create a Django superuser account:
```bash
docker-compose exec backend python manage.py createsuperuser
```

### Access the Application
- **Django Admin Panel:**
  http://localhost:8000/admin
- **Main Website:**
  http://localhost:3000
---
### How to Use the Service

1. To start using the service, you need to create bots on both telegram and bale then and obtain their **bot tokens**.
2. Add these tokens to the `Back-end/.env` file in the corresponding token configuration fields.
3. Add each bot as an **admin** to the channel where content will be published.
4. Once the bots are configured and added to the target channels, the service is fully ready to use.

After completing these steps, you can use all features of the service without limitations.

## 🤝 Contribution
Contributions are welcome!  
Please open an issue or submit a pull request.

---
# give a star if you find it useful :D

