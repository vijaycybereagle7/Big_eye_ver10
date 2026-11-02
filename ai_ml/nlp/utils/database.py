"""
Database integration for Cyber NLP Processor
Supports MongoDB and PostgreSQL for storing analysis results
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

try:
    import pymongo
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logging.warning("MongoDB driver not available. Install with: pip install pymongo")

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logging.warning("PostgreSQL driver not available. Install with: pip install psycopg2-binary")


class MongoDBStorage:
    """MongoDB storage for NLP analysis results"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", 
                 database_name: str = "cyber_nlp"):
        if not MONGODB_AVAILABLE:
            raise ImportError("MongoDB driver not available. Install pymongo with: pip install pymongo")
        
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.logger = logging.getLogger(__name__)
    
    def create_indexes(self):
        """Create database indexes for efficient querying"""
        try:
            # IOC collection indexes
            iocs_collection = self.db.iocs
            iocs_collection.create_index([("type", 1)])
            iocs_collection.create_index([("value", 1)])
            iocs_collection.create_index([("confidence", -1)])
            iocs_collection.create_index([("timestamp", -1)])
            iocs_collection.create_index([("source", 1)])
            
            # Threat intelligence collection indexes
            threat_collection = self.db.threat_intelligence
            threat_collection.create_index([("timestamp", -1)])
            threat_collection.create_index([("language", 1)])
            threat_collection.create_index([("threat_actors", 1)])
            threat_collection.create_index([("malware_families", 1)])
            
            # Email analysis collection indexes
            email_collection = self.db.email_analysis
            email_collection.create_index([("timestamp", -1)])
            email_collection.create_index([("classification", 1)])
            email_collection.create_index([("confidence", -1)])
            
            # Brand analysis collection indexes
            brand_collection = self.db.brand_analysis
            brand_collection.create_index([("timestamp", -1)])
            brand_collection.create_index([("domain", 1)])
            brand_collection.create_index([("suspicious_score", -1)])
            
            self.logger.info("Database indexes created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create indexes: {e}")
    
    def store_iocs(self, iocs: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Store extracted IOCs"""
        try:
            collection = self.db.iocs
            
            for ioc in iocs:
                ioc_document = {
                    **ioc,
                    "stored_at": datetime.now(),
                    "metadata": metadata or {}
                }
                collection.insert_one(ioc_document)
            
            self.logger.info(f"Stored {len(iocs)} IOCs")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store IOCs: {e}")
            return False
    
    def store_threat_intelligence(self, threat_intel: Dict[str, Any], 
                                original_text: str = None):
        """Store threat intelligence analysis"""
        try:
            collection = self.db.threat_intelligence
            
            document = {
                **threat_intel,
                "original_text": original_text,
                "stored_at": datetime.now()
            }
            
            result = collection.insert_one(document)
            self.logger.info(f"Stored threat intelligence with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            self.logger.error(f"Failed to store threat intelligence: {e}")
            return None
    
    def store_email_analysis(self, email_analysis: Dict[str, Any], 
                           subject: str = None, sender: str = None):
        """Store email analysis results"""
        try:
            collection = self.db.email_analysis
            
            document = {
                **email_analysis,
                "subject": subject,
                "sender": sender,
                "stored_at": datetime.now()
            }
            
            result = collection.insert_one(document)
            self.logger.info(f"Stored email analysis with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            self.logger.error(f"Failed to store email analysis: {e}")
            return None
    
    def store_brand_analysis(self, brand_analysis: Dict[str, Any]):
        """Store brand impersonation analysis"""
        try:
            collection = self.db.brand_analysis
            
            document = {
                **brand_analysis,
                "stored_at": datetime.now()
            }
            
            result = collection.insert_one(document)
            self.logger.info(f"Stored brand analysis with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            self.logger.error(f"Failed to store brand analysis: {e}")
            return None
    
    def query_iocs(self, filters: Dict[str, Any] = None, limit: int = 1000):
        """Query stored IOCs"""
        try:
            collection = self.db.iocs
            
            query = filters or {}
            cursor = collection.find(query).limit(limit)
            
            results = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc['_id'] = str(doc['_id'])
                results.append(doc)
            
            return results
        except Exception as e:
            self.logger.error(f"Failed to query IOCs: {e}")
            return []
    
    def query_threat_intelligence(self, filters: Dict[str, Any] = None, limit: int = 100):
        """Query threat intelligence data"""
        try:
            collection = self.db.threat_intelligence
            
            query = filters or {}
            cursor = collection.find(query).limit(limit).sort("timestamp", -1)
            
            results = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                results.append(doc)
            
            return results
        except Exception as e:
            self.logger.error(f"Failed to query threat intelligence: {e}")
            return []
    
    def get_ioc_statistics(self):
        """Get IOC statistics from database"""
        try:
            collection = self.db.iocs
            
            pipeline = [
                {
                    "$group": {
                        "_id": "$type",
                        "count": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"},
                        "max_confidence": {"$max": "$confidence"}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            results = list(collection.aggregate(pipeline))
            return [{"type": r["_id"], **r} for r in results]
        except Exception as e:
            self.logger.error(f"Failed to get IOC statistics: {e}")
            return []
    
    def delete_old_records(self, days: int = 30):
        """Delete records older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            collections = [self.db.iocs, self.db.threat_intelligence, 
                          self.db.email_analysis, self.db.brand_analysis]
            
            total_deleted = 0
            for collection in collections:
                result = collection.delete_many({"stored_at": {"$lt": cutoff_date}})
                total_deleted += result.deleted_count
            
            self.logger.info(f"Deleted {total_deleted} records older than {days} days")
            return total_deleted
        except Exception as e:
            self.logger.error(f"Failed to delete old records: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        self.client.close()


class PostgreSQLStorage:
    """PostgreSQL storage for NLP analysis results"""
    
    def __init__(self, host: str = "localhost", port: int = 5432, 
                 database: str = "cyber_nlp", user: str = None, password: str = None):
        if not POSTGRES_AVAILABLE:
            raise ImportError("PostgreSQL driver not available. Install psycopg2-binary with: pip install psycopg2-binary")
        
        self.connection_string = f"host={host} port={port} dbname={database}"
        if user:
            self.connection_string += f" user={user}"
        if password:
            self.connection_string += f" password={password}"
        
        self.logger = logging.getLogger(__name__)
        self._create_tables()
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def _create_tables(self):
        """Create necessary tables"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # IOC table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS iocs (
                            id SERIAL PRIMARY KEY,
                            type VARCHAR(50) NOT NULL,
                            value TEXT NOT NULL,
                            confidence FLOAT DEFAULT 0.0,
                            context TEXT,
                            source VARCHAR(50),
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            metadata JSONB
                        )
                    """)
                    
                    # Threat intelligence table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS threat_intelligence (
                            id SERIAL PRIMARY KEY,
                            language VARCHAR(10),
                            sentiment_score FLOAT DEFAULT 0.0,
                            threat_actors TEXT[],
                            malware_families TEXT[],
                            attack_vectors TEXT[],
                            iocs JSONB,
                            entities JSONB,
                            original_text TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Email analysis table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS email_analysis (
                            id SERIAL PRIMARY KEY,
                            classification VARCHAR(50),
                            confidence FLOAT DEFAULT 0.0,
                            phishing_indicators TEXT[],
                            suspicious_urls JSONB,
                            suspicious_attachments TEXT[],
                            analysis_details JSONB,
                            subject TEXT,
                            sender TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Brand analysis table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS brand_analysis (
                            id SERIAL PRIMARY KEY,
                            domain VARCHAR(255),
                            suspicious_score FLOAT DEFAULT 0.0,
                            potential_brands TEXT[],
                            suspicious_patterns TEXT[],
                            brand_similarity JSONB,
                            recommendation TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_iocs_type ON iocs(type)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_iocs_confidence ON iocs(confidence)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_timestamp ON threat_intelligence(timestamp)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_classification ON email_analysis(classification)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_brand_domain ON brand_analysis(domain)")
                    
                    conn.commit()
                    self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise
    
    def store_iocs(self, iocs: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Store extracted IOCs"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    for ioc in iocs:
                        cursor.execute("""
                            INSERT INTO iocs (type, value, confidence, context, source, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            ioc.get('type', ''),
                            ioc.get('value', ''),
                            ioc.get('confidence', 0.0),
                            ioc.get('context', ''),
                            ioc.get('source', ''),
                            json.dumps(metadata or {})
                        ))
                    conn.commit()
                    self.logger.info(f"Stored {len(iocs)} IOCs")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to store IOCs: {e}")
            return False
    
    def store_threat_intelligence(self, threat_intel: Dict[str, Any], 
                                original_text: str = None):
        """Store threat intelligence analysis"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO threat_intelligence 
                        (language, sentiment_score, threat_actors, malware_families, 
                         attack_vectors, iocs, entities, original_text)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        threat_intel.get('language', ''),
                        threat_intel.get('sentiment_score', 0.0),
                        threat_intel.get('threat_actors', []),
                        threat_intel.get('malware_families', []),
                        threat_intel.get('attack_vectors', []),
                        json.dumps(threat_intel.get('iocs', {})),
                        json.dumps(threat_intel.get('entities', {})),
                        original_text
                    ))
                    conn.commit()
                    self.logger.info("Stored threat intelligence")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to store threat intelligence: {e}")
            return False
    
    def store_email_analysis(self, email_analysis: Dict[str, Any], 
                           subject: str = None, sender: str = None):
        """Store email analysis results"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO email_analysis 
                        (classification, confidence, phishing_indicators, suspicious_urls,
                         suspicious_attachments, analysis_details, subject, sender)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        email_analysis.get('classification', ''),
                        email_analysis.get('confidence', 0.0),
                        email_analysis.get('phishing_indicators', []),
                        json.dumps(email_analysis.get('suspicious_urls', [])),
                        email_analysis.get('suspicious_attachments', []),
                        json.dumps(email_analysis.get('analysis_details', {})),
                        subject,
                        sender
                    ))
                    conn.commit()
                    self.logger.info("Stored email analysis")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to store email analysis: {e}")
            return False
    
    def store_brand_analysis(self, brand_analysis: Dict[str, Any]):
        """Store brand impersonation analysis"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO brand_analysis 
                        (domain, suspicious_score, potential_brands, suspicious_patterns,
                         brand_similarity, recommendation)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        brand_analysis.get('domain', ''),
                        brand_analysis.get('suspicious_score', 0.0),
                        brand_analysis.get('potential_brands', []),
                        brand_analysis.get('suspicious_patterns', []),
                        json.dumps(brand_analysis.get('brand_similarity', {})),
                        brand_analysis.get('recommendation', '')
                    ))
                    conn.commit()
                    self.logger.info("Stored brand analysis")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to store brand analysis: {e}")
            return False
    
    def query_iocs(self, filters: Dict[str, Any] = None, limit: int = 1000):
        """Query stored IOCs"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    where_clauses = []
                    params = []
                    
                    if filters:
                        if 'type' in filters:
                            where_clauses.append("type = %s")
                            params.append(filters['type'])
                        
                        if 'confidence_min' in filters:
                            where_clauses.append("confidence >= %s")
                            params.append(filters['confidence_min'])
                        
                        if 'source' in filters:
                            where_clauses.append("source = %s")
                            params.append(filters['source'])
                    
                    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                    
                    query = f"""
                        SELECT id, type, value, confidence, context, source, 
                               timestamp, metadata
                        FROM iocs
                        {where_sql}
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """
                    params.append(limit)
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    # Convert to regular dict for JSON serialization
                    return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Failed to query IOCs: {e}")
            return []
    
    def get_ioc_statistics(self):
        """Get IOC statistics from database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT type, COUNT(*) as count, 
                               AVG(confidence) as avg_confidence,
                               MAX(confidence) as max_confidence
                        FROM iocs
                        GROUP BY type
                        ORDER BY count DESC
                    """)
                    
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Failed to get IOC statistics: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        pass  # Connection closes automatically with context manager


class DatabaseManager:
    """Unified database manager for both MongoDB and PostgreSQL"""
    
    def __init__(self, db_type: str = "mongodb", **kwargs):
        """Initialize database manager
        
        Args:
            db_type: "mongodb" or "postgresql"
            **kwargs: Connection parameters
        """
        self.db_type = db_type.lower()
        
        if self.db_type == "mongodb":
            if not MONGODB_AVAILABLE:
                raise ImportError("MongoDB not available. Install pymongo with: pip install pymongo")
            
            connection_string = kwargs.get('connection_string', 'mongodb://localhost:27017/')
            database_name = kwargs.get('database_name', 'cyber_nlp')
            self.storage = MongoDBStorage(connection_string, database_name)
            
        elif self.db_type == "postgresql":
            if not POSTGRES_AVAILABLE:
                raise ImportError("PostgreSQL not available. Install psycopg2-binary with: pip install psycopg2-binary")
            
            self.storage = PostgreSQLStorage(**kwargs)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        self.logger = logging.getLogger(__name__)
    
    def create_indexes(self):
        """Create database indexes (MongoDB only)"""
        if self.db_type == "mongodb":
            return self.storage.create_indexes()
        else:
            self.logger.warning("Index creation not supported for PostgreSQL")
    
    def store_analysis_results(self, results: Dict[str, Any]):
        """Store comprehensive analysis results"""
        try:
            success_count = 0
            
            # Store IOCs
            if 'iocs' in results:
                metadata = {'source': 'cyber_nlp_processor'}
                if self.storage.store_iocs(results['iocs'], metadata):
                    success_count += 1
            
            # Store threat intelligence
            if 'threat_intelligence' in results:
                threat_data = results['threat_intelligence']
                original_text = threat_data.get('original_text', '')
                if self.storage.store_threat_intelligence(threat_data, original_text):
                    success_count += 1
            
            # Store email analysis
            if 'email_analysis' in results:
                email_data = results['email_analysis']
                if self.storage.store_email_analysis(
                    email_data,
                    email_data.get('subject', ''),
                    email_data.get('sender', '')
                ):
                    success_count += 1
            
            # Store brand analysis
            if 'brand_analysis' in results:
                if self.storage.store_brand_analysis(results['brand_analysis']):
                    success_count += 1
            
            self.logger.info(f"Successfully stored {success_count}/4 analysis components")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to store analysis results: {e}")
            return False
    
    def query_all(self, ioc_filters: Dict[str, Any] = None, limit: int = 1000):
        """Query all stored data"""
        results = {}
        
        try:
            results['iocs'] = self.storage.query_iocs(ioc_filters, limit)
            results['threat_intelligence'] = self.storage.query_threat_intelligence(limit=limit//10)
            results['ioc_statistics'] = self.storage.get_ioc_statistics()
            
            return results
        except Exception as e:
            self.logger.error(f"Failed to query data: {e}")
            return results
    
    def close(self):
        """Close database connection"""
        if hasattr(self.storage, 'close'):
            self.storage.close()
