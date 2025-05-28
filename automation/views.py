from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from  system_management.permissions import check_role_permission_on_module_decorator
from django.contrib import messages
from .models import BulkUploadJob


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def not_found(request):

    return render(request, "automation/not_found.html")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def view_job_detail(request, id):
    try:
        job = BulkUploadJob.objects.get(id=id)
        job_columns = []
        job_data = []
        error_logs = job.error_log
        if len(error_logs) > 0:
            job_columns += [ col for col in error_logs[0].keys() if col not in ("data")]
        
            sample_data = error_logs[0]['data']
            other_cols = [col for col in sample_data.keys()]

            for error_log in error_logs:
                row_data = []
                row_data.append(error_log['row'])
                row_data.append(error_log['error'])
                data = error_log['data']
                for key in other_cols:
                    row_data.append(data[key])
                
                job_data.append(row_data)
            
            job_columns += other_cols
                
        context = {
            "upload_job": job,
            "job_columns": job_columns,
            "category": job.category,
            "job_data": job_data
        }
        return render(request, "automation/upload_job_details.html", context=context)
    except BulkUploadJob.DoesNotExist as e:
        messages.error(request, f"Page not found: [ERROR]: {str(e)}")
        return redirect("automation:index")
    

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def clear_job_data(request, id):
    try:
        job = BulkUploadJob.objects.get(id=id)
        error_logs = job.error_log
        if len(error_logs) > 0:
            job.error_log = []
            job.failure_count = 0
            job.save()
            messages.success(request, f"Job failed {job.category} records cleared successfully")
        return redirect(reverse("automation:job_detail", args=(id, )))        
    except BulkUploadJob.DoesNotExist as e:
        messages.error(request, f"Page not found: [ERROR]: {str(e)}")
        return redirect("automation:index")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def delete_upload_job(request, id):
    try:
        job = BulkUploadJob.objects.get(id=id)
        category = job.category
        job.delete()
        messages.success(request, f"{category} upload job deleted successfully")
        if category == "ICBT":
            redirect_url = reverse('trade:icbt-list')
            return redirect(f"{redirect_url}#icbt-upload-job") 
        else:
            return redirect("automation:index")     
    except BulkUploadJob.DoesNotExist as e:
        messages.error(request, f"Page not found: [ERROR]: {str(e)}")
        return redirect("automation:index")

    