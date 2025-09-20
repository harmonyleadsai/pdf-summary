import logging
from datetime import datetime
from typing import Dict
import app.utils.db as db_utils
import json
from app.utils.utility_functions import clean_for_json
from app.config import settings

logger = logging.getLogger(__name__)

async def user_log_processing(log_payload: Dict):
    logger.info("Starting to log the user activity into Database")

    try:
        # Step 1: fetch row by all 3 conditions
        """res = (
            supabase.table("user_log")
            .select("user_id, pdf_id, analysis_id, qa_log")
            .eq("user_id", log_payload.get("user_id"))
            .eq("pdf_id", log_payload.get("pdf_id"))
            .eq("analysis_id", log_payload.get("analysis_id"))
            .execute()
        )"""
        if db_utils.db_pool is None:
            logger.error("No db pool configured")

        async with db_utils.db_pool.acquire() as conn:
            user_log_res = await conn.fetchrow(settings.SP_USER_LOG_FETCH_QUERY, log_payload.get("filename"), log_payload.get("user_id"))

            #print(user_log_res)
            if user_log_res and len(user_log_res.get("qa_log")) > 0:
                # Row exists
                qa_log = json.loads(user_log_res.get("qa_log") or [])

                # Append new entry
                qa_log.append(log_payload.get("qa_log"))

                qa_log = clean_for_json(qa_log)

                # Update existing row
                upd = await conn.execute(
                    settings.SP_UPDATE_USER_LOG_QUERY, json.dumps(qa_log), datetime.now(), log_payload.get("user_id"), log_payload.get("filename")
                )


                if not upd or len(upd) == 0:
                    logger.error("Failed to update log for user: %s", log_payload.get("user_id"))
                else:
                    logger.info("Updated log for user %s", log_payload.get("user_id"))

            else:

                if 'qa_log' in log_payload:
                    log_payload['qa_log'] = clean_for_json(log_payload['qa_log'])
                    log_payload['qa_log'] = json.dumps(log_payload['qa_log'])

                # No row found → insert new
                #log_payload = clean_for_json(log_payload)

                columns = ", ".join(log_payload.keys())
                placeholders = ", ".join(f"${i + 1}" for i in range(len(log_payload)))
                values = list(log_payload.values())

                query = f"INSERT INTO user_log ({columns}) VALUES ({placeholders}) RETURNING user_id"

                insert_res = await conn.fetchrow(query, *values)

                if not insert_res or len(insert_res.get("user_id")) == 0:
                    logger.error("Failed to insert log for user: %s", log_payload.get("user_id"))
                else:
                    logger.info("Inserted log for user %s", log_payload.get("user_id"))



    except Exception as e:
        logger.exception(f"Error inserting log for user {log_payload.get("user_id")}: {e}")
