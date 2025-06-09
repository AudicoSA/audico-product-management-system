import os
import uuid
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStep(Enum):
    """Individual workflow steps"""
    UPLOAD = "upload"
    EXTRACT = "extract"
    PARSE = "parse"
    VALIDATE = "validate"
    COMPARE = "compare"
    AUTOMATION = "automation"
    COMPLETE = "complete"

@dataclass
class WorkflowResult:
    """Complete workflow execution result"""
    workflow_id: str
    status: WorkflowStatus
    current_step: WorkflowStep
    started_at: str
    completed_at: Optional[str] = None
    total_duration: Optional[float] = None

    # Step results
    upload_result: Optional[Dict] = None
    extraction_result: Optional[Dict] = None
    parsing_result: Optional[Dict] = None
    validation_result: Optional[Dict] = None
    comparison_result: Optional[Dict] = None
    automation_result: Optional[Dict] = None

    # Summary
    pdf_filename: Optional[str] = None
    products_extracted: int = 0
    products_missing: int = 0
    products_created: int = 0
    products_updated: int = 0

    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class WorkflowManager:
    """Orchestrate the complete product management workflow"""

    def __init__(self, opencart_client):
        self.opencart_client = opencart_client
        self.workflows = {}  # In-memory storage (would use database in production)

    def start_workflow(self, pdf_file, options: Dict = None) -> str:
        """Start a new workflow execution"""
        workflow_id = str(uuid.uuid4())

        # Initialize workflow result
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            current_step=WorkflowStep.UPLOAD,
            started_at=datetime.now().isoformat(),
            pdf_filename=pdf_file.filename if hasattr(pdf_file, 'filename') else 'unknown.pdf'
        )

        # Store workflow
        self.workflows[workflow_id] = workflow_result

        # Default options
        if options is None:
            options = {}

        default_options = {
            'auto_create_missing': True,
            'auto_update_prices': False,
            'validation_threshold': 0.7,
            'price_tolerance_percent': 5.0,
            'batch_size': 10,
            'dry_run': False
        }
        default_options.update(options)

        # Execute workflow asynchronously (in a real app, this would be queued)
        try:
            self._execute_workflow(workflow_id, pdf_file, default_options)
        except Exception as e:
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.errors.append(f"Workflow execution failed: {str(e)}")

        return workflow_id

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current workflow status"""
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]
        return asdict(workflow)

    def _execute_workflow(self, workflow_id: str, pdf_file, options: Dict):
        """Execute the complete workflow"""
        workflow = self.workflows[workflow_id]
        start_time = datetime.now()

        try:
            workflow.status = WorkflowStatus.PROCESSING

            # Step 1: Upload and save PDF
            workflow.current_step = WorkflowStep.UPLOAD
            upload_result = self._step_upload_pdf(pdf_file)
            workflow.upload_result = upload_result

            if not upload_result['success']:
                raise Exception(f"Upload failed: {upload_result['error']}")

            # Step 2: Extract text from PDF
            workflow.current_step = WorkflowStep.EXTRACT
            extraction_result = self._step_extract_text(upload_result['filepath'])
            workflow.extraction_result = extraction_result

            if not extraction_result['success']:
                raise Exception(f"Text extraction failed: {extraction_result['error']}")

            # Step 3: Parse products from text
            workflow.current_step = WorkflowStep.PARSE
            parsing_result = self._step_parse_products(extraction_result['text'])
            workflow.parsing_result = parsing_result

            if not parsing_result['success']:
                raise Exception(f"Product parsing failed: {parsing_result['error']}")

            workflow.products_extracted = parsing_result['products_found']

            # Step 4: Validate and clean product data
            workflow.current_step = WorkflowStep.VALIDATE
            validation_result = self._step_validate_products(parsing_result['products'])
            workflow.validation_result = validation_result

            # Filter products based on validation threshold
            valid_products = self._filter_valid_products(
                parsing_result['products'], 
                options['validation_threshold']
            )

            if not valid_products:
                workflow.warnings.append("No products passed validation threshold")
                workflow.status = WorkflowStatus.COMPLETED
                return

            # Step 5: Compare with OpenCart inventory
            workflow.current_step = WorkflowStep.COMPARE
            comparison_result = self._step_compare_products(valid_products, options)
            workflow.comparison_result = comparison_result

            if not comparison_result['success']:
                raise Exception(f"Product comparison failed: {comparison_result['error']}")

            workflow.products_missing = len(comparison_result['missing_products'])

            # Step 6: Automation (create/update products)
            workflow.current_step = WorkflowStep.AUTOMATION

            if not options['dry_run']:
                automation_result = self._step_automate_products(comparison_result, options)
                workflow.automation_result = automation_result

                if automation_result['success']:
                    workflow.products_created = automation_result.get('created_count', 0)
                    workflow.products_updated = automation_result.get('updated_count', 0)
                else:
                    workflow.warnings.append(f"Automation had issues: {automation_result.get('error', 'Unknown error')}")
            else:
                workflow.automation_result = {
                    'success': True,
                    'message': 'Dry run - no products were actually created/updated',
                    'would_create': len(comparison_result['missing_products']),
                    'would_update': len(comparison_result.get('price_differences', []))
                }

            # Cleanup
            if upload_result.get('filepath') and os.path.exists(upload_result['filepath']):
                os.unlink(upload_result['filepath'])

            # Complete workflow
            workflow.current_step = WorkflowStep.COMPLETE
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now().isoformat()
            workflow.total_duration = (datetime.now() - start_time).total_seconds()

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(str(e))
            workflow.completed_at = datetime.now().isoformat()
            workflow.total_duration = (datetime.now() - start_time).total_seconds()

    def _step_upload_pdf(self, pdf_file) -> Dict:
        """Step 1: Upload and save PDF"""
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                pdf_file.save(tmp_file.name)

                return {
                    'success': True,
                    'filepath': tmp_file.name,
                    'filename': pdf_file.filename if hasattr(pdf_file, 'filename') else 'unknown.pdf',
                    'size': os.path.getsize(tmp_file.name)
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _step_extract_text(self, pdf_path: str) -> Dict:
        """Step 2: Extract text from PDF"""
        try:
            from pdf_processor.ocr_extractor import OCRExtractor

            extractor = OCRExtractor()
            result = extractor.extract_text_from_pdf(pdf_path)

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _step_parse_products(self, text: str) -> Dict:
        """Step 3: Parse products from extracted text"""
        try:
            from pdf_processor.data_parser import DataParser

            parser = DataParser()
            result = parser.parse_text(text)

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _step_validate_products(self, products: List[Dict]) -> Dict:
        """Step 4: Validate and clean product data"""
        try:
            from pdf_processor.data_validator import DataValidator

            validator = DataValidator()

            # Clean each product
            cleaned_products = []
            for product in products:
                cleaned_product = validator.clean_product_data(product)
                cleaned_products.append(cleaned_product)

            # Validate the batch
            validation_result = validator.validate_product_batch(cleaned_products)
            validation_result['cleaned_products'] = cleaned_products

            return validation_result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _step_compare_products(self, products: List[Dict], options: Dict) -> Dict:
        """Step 5: Compare products with OpenCart inventory"""
        try:
            from comparison_engine.product_comparator import ProductComparator

            comparator = ProductComparator(self.opencart_client)
            comparator.price_tolerance_percent = options['price_tolerance_percent']

            result = comparator.compare_products(products)

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _step_automate_products(self, comparison_result: Dict, options: Dict) -> Dict:
        """Step 6: Automate product creation/updates"""
        try:
            from automation_engine.product_automator import ProductAutomator

            automator = ProductAutomator(self.opencart_client)
            automator.batch_size = options['batch_size']

            created_count = 0
            updated_count = 0
            errors = []

            # Create missing products
            if options['auto_create_missing'] and comparison_result['missing_products']:
                create_result = automator.create_products_batch(comparison_result['missing_products'])

                if create_result['success']:
                    created_count = create_result['summary']['successful_creations']
                else:
                    errors.append(f"Product creation failed: {create_result.get('error', 'Unknown error')}")

            return {
                'success': len(errors) == 0,
                'created_count': created_count,
                'updated_count': updated_count,
                'errors': errors,
                'message': f"Created {created_count} products, updated {updated_count} products"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _filter_valid_products(self, products: List[Dict], threshold: float) -> List[Dict]:
        """Filter products based on validation confidence threshold"""
        # For now, return all products since we don't have detailed validation scores per product
        return products

    def get_workflow_summary(self, workflow_id: str) -> Optional[Dict]:
        """Get a summary of workflow execution"""
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]

        return {
            'workflow_id': workflow_id,
            'status': workflow.status.value,
            'current_step': workflow.current_step.value,
            'pdf_filename': workflow.pdf_filename,
            'duration': workflow.total_duration,
            'summary': {
                'products_extracted': workflow.products_extracted,
                'products_missing': workflow.products_missing,
                'products_created': workflow.products_created,
                'products_updated': workflow.products_updated
            },
            'has_errors': len(workflow.errors) > 0,
            'has_warnings': len(workflow.warnings) > 0,
            'error_count': len(workflow.errors),
            'warning_count': len(workflow.warnings)
        }

    def list_workflows(self, limit: int = 50) -> List[Dict]:
        """List recent workflows"""
        workflows = []

        for workflow_id, workflow in list(self.workflows.items())[-limit:]:
            workflows.append(self.get_workflow_summary(workflow_id))

        return sorted(workflows, key=lambda x: x.get('workflow_id', ''), reverse=True)
