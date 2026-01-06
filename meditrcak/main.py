from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import threading

from app.config.settings import settings
from app.auth.routes import router as auth_router
from app.patients.routes import router as patients_router
from app.medications.routes import router as medications_router
from app.adherence.routes import router as adherence_router
from app.reminders.routes import router as reminders_router
from app.analytics import router as analytics_router
from app.agent.router import router as agent_router
from app.agent.utils.text_to_speech import router as tts_router
from app.database.init_db import init_db, populate_from_local_db

# Disable all logging
# logging.disable(logging.CRITICAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup: Initialize database
    init_db()

    # Check if database already has data
    from app.database.db import get_db
    from app.patients.models import Patient
    from sqlalchemy.orm import Session
    
    db: Session = next(get_db())
    try:
        patient_count = db.query(Patient).count()
        if patient_count > 0:
            print(f"📊 Database already populated with {patient_count} patients. Skipping population.")
        else:
            # Populate database with sample data
            try:
                print("🌱 Populating database with sample data...")
                result = populate_from_local_db()
                print(f"✅ Database population completed! Result: {result}")
            except Exception as e:
                print(f"⚠️  Database population failed: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the app startup if population fails
    finally:
        db.close()
    
    # Pre-load vector store and embeddings at startup
    try:
        print("🔄 Loading vector store and embeddings model...")
        from app.agent.rag.vector_store import get_vectorstore
        vectorstore = get_vectorstore()
        print(f"✅ Vector store loaded successfully! Index size: {vectorstore.index.ntotal} documents")
    except Exception as e:
        print(f"⚠️  Vector store loading failed: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail the app startup if vector store fails

    # Start automated reminder scheduler in background thread
    try:
        print("🚀 Starting automated reminder scheduler...")
        from automated_reminder_scheduler import AutomatedReminderScheduler
        
        def run_scheduler():
            scheduler = AutomatedReminderScheduler()
            scheduler.run()
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("✅ Automated reminder scheduler started in background!")
    except Exception as e:
        print(f"⚠️  Reminder scheduler startup failed: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail the app startup if scheduler fails

    yield
    # Shutdown: cleanup if needed


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure Jinja2 templates
# templates = Jinja2Templates(directory="templates")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(medications_router)
app.include_router(adherence_router)
app.include_router(reminders_router)
app.include_router(analytics_router)
app.include_router(agent_router)
app.include_router(tts_router)



@app.get("/debug/tables")
async def get_database_tables():
    """Debug endpoint to get all table names and sample data."""
    from sqlalchemy import text
    from app.database.db import engine
    
    try:
        with engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result.fetchall()]
            
            table_data = {}
            for table in tables:
                if table.startswith('sqlite_'):
                    continue
                    
                try:
                    # Get column info
                    columns_result = conn.execute(text(f"PRAGMA table_info({table});"))
                    columns = [row[1] for row in columns_result.fetchall()]
                    
                    # Get sample data (first 50 rows for better detail)
                    data_result = conn.execute(text(f"SELECT * FROM {table} LIMIT 50;"))
                    rows = [dict(zip(columns, row)) for row in data_result.fetchall()]
                    
                    # Get total count
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count = count_result.fetchone()[0]
                    
                    table_data[table] = {
                        'columns': columns,
                        'sample_data': rows,
                        'total_count': count
                    }
                except Exception as e:
                    table_data[table] = {
                        'error': str(e),
                        'columns': [],
                        'sample_data': [],
                        'total_count': 0
                    }
            
            return {
                'tables': list(table_data.keys()),
                'data': table_data
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to MediTrack-AI API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # Use string path instead of app object
        host="0.0.0.0", 
        port=8000,
        reload=False  # Disable auto-reload to prevent constant restarts
    )
