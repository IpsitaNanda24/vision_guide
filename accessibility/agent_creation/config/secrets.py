import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger("omnisense-secrets")

def load_secrets():
    """
    Loads environment variables from a local .env file.
    If not running locally (no API keys found) and deployed to GCP, 
    attempts to fetch the keys from GCP Secret Manager.
    """
    # 1. Attempt to load local .env first
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info("Loaded local .env file.")
        
    # 2. Check if API keys are missing (indicates we might be in the cloud without env vars set)
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        # We assume GOOGLE_CLOUD_PROJECT is set in GCP environments like Cloud Run / App Engine
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        
        if project_id:
            logger.info(f"Attempting to fetch secrets from GCP Secret Manager for project: {project_id}")
            try:
                from google.cloud import secretmanager
                client = secretmanager.SecretManagerServiceClient()
                
                def fetch_secret(secret_id):
                    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
                    try:
                        response = client.access_secret_version(request={"name": name})
                        return response.payload.data.decode("UTF-8")
                    except Exception as e:
                        logger.warning(f"Failed to load {secret_id} from Secret Manager: {e}")
                        return None

                gemini_key = fetch_secret("GEMINI_API_KEY")
                if gemini_key:
                    os.environ["GEMINI_API_KEY"] = gemini_key
                    logger.info("Loaded GEMINI_API_KEY from Secret Manager.")
                
                google_key = fetch_secret("GOOGLE_API_KEY")
                if google_key:
                    os.environ["GOOGLE_API_KEY"] = google_key
                    logger.info("Loaded GOOGLE_API_KEY from Secret Manager.")
                    
            except ImportError:
                logger.error("google-cloud-secret-manager is not installed. Cannot fetch secrets.")
            except Exception as e:
                logger.error(f"Error accessing Secret Manager: {e}")
        else:
            logger.warning("No API keys found and GOOGLE_CLOUD_PROJECT is not set. Agents may fail to initialize.")
