import csv
import os
from decimal import Decimal
from django.http import HttpRequest
from django.conf import settings

from .models import (IndustrialZone, PartitionedPlot, 
                    IndustryEconomicZone, AllocatedPlot,
                    CompanyProfile, CompanySite, 
                    IndustryContractPayment,
                    PaymentInstallmentTransaction,
                    ContractPaymentInstallment)
from django.utils import timezone


def get_base_domain(request):
    # scheme = 'https' if request.is_secure() else 'http'
    host = settings.PUBLIC_IP
    scheme = "http"
    base_domain = f"{scheme}://{host}:{settings.WEBSERVER_PORT}"
    try:
        if int(settings.WEBSERVER_PORT) == 80:
            base_domain = f"{scheme}://{host}"
    except:
        pass
    return base_domain

def load_countries():
    DATA_PATH_FILE = os.path.join(os.getcwd(), "all_countries.csv")
    with open(DATA_PATH_FILE, mode='r', newline='', encoding='utf-8') as file_reader:
        csv_reader = csv.reader(file_reader)
        countries = []
        for row in csv_reader:
            countries.append(row[0])
    return countries[1:]


def get_zones_and_partitioned_plots_in_park(park_id=None):
    """
    Get all zones and partitioned plots for particular park when park_id is given else all zones in the park
    """
    zones = []
    partitioned_plots = []
    if park_id is not None:
        park = IndustryEconomicZone.objects.filter(id=park_id).first()
        if park is not None:
            partitioned_plots_ = PartitionedPlot.objects.filter(park=park).order_by("zone__name")
        else:
            partitioned_plots_ = []
    else:
        partitioned_plots_ = PartitionedPlot.objects.all().order_by("zone__name")
    
    found_zones = []
    for plot in partitioned_plots_:
            if f"{plot.zone.name}_{plot.park.id}_{plot.park.name}" not in found_zones:
                found_zones.append(f"{plot.zone.name}_{plot.park.id}_{plot.park.name}")
                zones.append({
                    "id": plot.zone.id,
                    "name": plot.zone.name,
                    "park_id": plot.park.id,
                    "park_name": f"{plot.park.name} {plot.park.category}"
                })

            if plot.is_allocated == False:
                partitioned_plots.append({
                        "id": plot.id,
                        "plot_number": plot.plot_number,
                        "plot_upi": plot.partitioned_plot_upi,
                        "upi_status": plot.upi_status,
                        "zone_id": plot.zone.id,
                        "zone_name": plot.zone.name,
                        "plot_size": round(float(plot.plot_size), 5),
                        "park_id": plot.park.id,
                        "park_name": f"{plot.park.name} {plot.park.category}"
                    })
    
    return zones, partitioned_plots

def record_allocated_plot_from_request(request, land_request):
    try:
        plot_upi = request.POST.get("plot_upi", "")
        upi_status = request.POST.get("upi_status")
        land_title_status = request.POST.get("land_title_status")
        date_of_letter_addressed_to_nla = request.POST.get("date_of_letter_addressed_to_nla", None)
        park_id = request.POST.get("park", -1)
        zoning_id = request.POST.get("zone", -1)
        plots_ids = request.POST.getlist("partitioned_plots[]", [])

        park = IndustryEconomicZone.objects.get(id=park_id)
        zoning = IndustrialZone.objects.get(id=zoning_id)
        partition_plots = PartitionedPlot.objects.filter(id__in=plots_ids)

        if not len(date_of_letter_addressed_to_nla.strip()) > 2:
            date_of_letter_addressed_to_nla = None

        if len(partition_plots) > 0:
            allocated_plot = AllocatedPlot(
                allocated_plot_upi=plot_upi,
                upi_status=upi_status,
                land_title_status=land_title_status,
                date_of_letter_addressed_to_nla=date_of_letter_addressed_to_nla,
                park=park,
                zone=zoning,
                land_request=land_request,
                land_owner=land_request.land_owner
            )

            allocated_plot.save()
            allocated_size = 0
            for plot in partition_plots:
                plot.allocated_plot= allocated_plot
                plot.is_allocated = True
                plot.save()
                allocated_size += plot.plot_size
            allocated_plot.plot_size=allocated_size
            allocated_plot.save()

            CompanySite.objects.create(
                company=land_request.land_owner,
                province=park.province,
                district=park.district,
                sector=park.sector,
                cell=park.cell,
                allocated_plot=allocated_plot
            )
        else:
            return False

        return True
    except Exception as e: 
        print(f"\n[ERROR]: {str(e)}\n")
        return False

def record_industry_in_plot_from_request(request):
    try:
        tin_number = request.POST.get("industry", " || ").split("||")[0]
        occupied_space = request.POST.get("occupied_space")
        longitude = request.POST.get("longitude", "")
        latitude = request.POST.get("latitude", "")
        province = request.POST.get("province")
        district = request.POST.get("district")
        sector = request.POST.get("sector")
        cell = request.POST.get("cell")
        investment_amount = request.POST.get("investment_amount")
        investment_currency = request.POST.get("investment_currency")
        allocated_plot = request.POST.get("allocated_plot")

        industry = CompanyProfile.objects.get(tin_number=tin_number)
        allocated_plot = AllocatedPlot.objects.get(id=allocated_plot)

        if len(longitude.strip()) < 2:
            longitude = None
        if len(latitude.strip()) < 2:
            latitude = None
        
        if len(occupied_space.strip()) < 2:
            occupied_space = None
        
        if len(investment_amount.strip()) < 2:
            investment_amount = None
            investment_currency = None

        CompanySite.objects.create(
            company=industry,
            longitude=longitude,
            latitude=latitude,
            province=province,
            district=district,
            sector=sector,
            cell=cell,
            occupied_space=occupied_space,
            investment_amount=investment_amount,
            investment_currency=investment_currency,
            allocated_plot=allocated_plot
        )

        return True
    except Exception as e: 
        print(f"\n[ERROR]: {str(e)}\n")
        return False

def convert_datetime_timezone(naive_datetime):
    # Make it timezone-aware using Django's timezone
    aware_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone()) 
    return aware_datetime

def create_payment_installment(contract_payment: IndustryContractPayment, installments_dates: list):
    """
    The function for creating payment installments
    params:
        - installments_dates: list of dates for the payment of installments in order from the initial payment
        - contract_payment: the payment of contract instance
    """
    if len(installments_dates) < 1:
        raise ValueError("You should provide the list of dates for payment installments")
    
    created_installments = []
    total_amount = 0
    try:
        if len(installments_dates) == 1:
            created_installments.append(
                ContractPaymentInstallment.objects.create(
                    contract_payment=contract_payment,
                    expected_payment_date=installments_dates[0],
                    expected_payment_amount=contract_payment.total_amount_to_pay
                )
            )
            total_amount += contract_payment.total_amount_to_pay
        else:
            thirty_perc = round(contract_payment.total_amount_to_pay * 30/100, 2)
            remaining = contract_payment.total_amount_to_pay - thirty_perc
            created_installments.append(
                ContractPaymentInstallment.objects.create(
                    contract_payment=contract_payment,
                    expected_payment_date=installments_dates[0],
                    expected_payment_amount=thirty_perc
                )
            )
            total_amount += thirty_perc
            remaining_split = remaining / len(installments_dates[1:]) # splitting equally the remaining amount into remaining installments
            for next_date in installments_dates[1:]:
                remaining_split = round(remaining_split + remaining_split * 5/100, 2)
                total_amount += remaining_split
                created_installments.append(
                    ContractPaymentInstallment.objects.create(
                        contract_payment=contract_payment,
                        expected_payment_date=next_date,
                        expected_payment_amount=remaining_split
                        )
                )
                remaining_split = created_installments[-1].expected_payment_amount

        return True, total_amount, "Payment installments created successfully"
    except Exception as e:
        for installment in created_installments:
            installment.delete()
        return False, total_amount, f"{str(e)}"

def use_sulpus_paid_amount_for_other_installments(installment: ContractPaymentInstallment, sulpus_amount, transaction: PaymentInstallmentTransaction):
    updated = False
    if installment.actual_paid_amount is None:
        installment.actual_paid_amount = 0
    amount_to_pay = installment.expected_payment_amount - installment.actual_paid_amount

    if amount_to_pay >= sulpus_amount:
        installment.actual_paid_amount += sulpus_amount
        installment.actual_payment_date = transaction.payment_date
        installment.updated_date = timezone.now()
        updated = True
        sulpus_amount = 0
    elif amount_to_pay > 0:
        sulpus_amount = sulpus_amount - amount_to_pay
        installment.actual_paid_amount += amount_to_pay
        installment.actual_payment_date = transaction.payment_date
        installment.updated_date = timezone.now()
        updated = True
    
    if updated:
        if (installment.expected_payment_amount - installment.actual_paid_amount) == 0:
            installment.payment_status = "FULLY PAID"
        else:
            installment.payment_status = "PARTIALLY PAID"
        installment.save()
    
    return updated, sulpus_amount, installment


def clear_installment_and_payment(transaction: PaymentInstallmentTransaction, installment: ContractPaymentInstallment):
    refund_transaction = None
    try:
        updated = False
        if installment.actual_paid_amount is None:
            installment.actual_paid_amount = 0
        
        amount_to_pay = installment.expected_payment_amount - installment.actual_paid_amount

        suplus_amount = 0
        if amount_to_pay >= Decimal(transaction.payment_amount):
            installment.actual_paid_amount += Decimal(transaction.payment_amount)
            installment.actual_payment_date = transaction.payment_date
            installment.updated_date = timezone.now()
            updated = True
        elif amount_to_pay > 0:
            suplus_amount = Decimal(transaction.payment_amount) - amount_to_pay
            installment.actual_paid_amount += amount_to_pay
            installment.actual_payment_date = transaction.payment_date
            installment.updated_date = timezone.now()
            updated = True
        
        if updated:
            if (installment.expected_payment_amount - installment.actual_paid_amount) == 0:
                installment.payment_status = "FULLY PAID"
            else:
                installment.payment_status = "PARTIALLY PAID"
            installment.save()

            next_payment_date = None
            paid_penalties = 0
            if suplus_amount > 0:
                other_installments = list(ContractPaymentInstallment.objects.filter(
                    contract_payment=installment.contract_payment,
                    payment_status__in=("PARTIALLY PAID", "NOT PAID")).exclude(id=installment.id).order_by("expected_payment_date"))
                
                for index, other_installment in enumerate(other_installments):
                    _, suplus_amount, installment_returned = use_sulpus_paid_amount_for_other_installments(other_installment, suplus_amount, transaction)
                    if installment_returned.payment_status == "PARTIALLY PAID":
                        next_payment_date = installment_returned.expected_payment_date
                        break
                    elif suplus_amount == 0 and installment_returned.payment_status == "FULLY PAID":
                        if index < len(other_installments) - 1:
                            next_payment_date = other_installments[index + 1].expected_payment_date
                        break
                
                if suplus_amount > 0: # clear the penalaties if there are some using the remaining amount
                    installment_with_penalties = ContractPaymentInstallment.objects.filter(contract_payment=installment.contract_payment, accrued_penalties__gt=0)
                    for penalty in installment_with_penalties:
                        if penalty.paid_penalties is None:
                            penalty.paid_penalties = 0
                        amount_to_pay = penalty.accrued_penalties - penalty.paid_penalties
                        if amount_to_pay >= suplus_amount:
                            paid_penalties += suplus_amount
                            penalty.paid_penalties += suplus_amount 
                            suplus_amount = 0
                        else:
                            paid_penalties += amount_to_pay
                            penalty.paid_penalties += amount_to_pay
                            suplus_amount = suplus_amount - amount_to_pay
                        penalty.save()

                        if suplus_amount == 0:
                            break
                    if suplus_amount > 0: # this amount must be refunded
                        transaction.refund_amount = suplus_amount
                        refund_transaction = transaction.id
                        transaction.save()

            elif suplus_amount == 0 and installment.payment_status == "FULLY PAID":
                other_installment = ContractPaymentInstallment.objects.filter(
                    contract_payment=installment.contract_payment,
                    payment_status__in=("PARTIALLY PAID", "NOT PAID")).exclude(id=installment.id).order_by("expected_payment_date").first()
                next_payment_date = other_installment.expected_payment_date if other_installment else None
            elif installment.payment_status == "PARTIALLY PAID":
                next_payment_date = installment.expected_payment_date
            
            payment = installment.contract_payment
            payment.next_payment_date = next_payment_date
            if payment.total_amount_paid is None:
                payment.total_amount_paid = 0
            payment.total_amount_paid += (Decimal(transaction.payment_amount) - suplus_amount)
            if payment.paid_penalties is None:
                payment.paid_penalties = 0
            payment.paid_penalties += paid_penalties 
            payment.updated_date = timezone.now()
            if payment.total_amount_unpaid is None:
                payment.total_amount_unpaid = 0
            payment.total_amount_unpaid = payment.total_amount_to_pay - payment.total_amount_paid

            if payment.total_amount_to_pay == payment.total_amount_paid:
                payment.payment_status = "FULLY PAID"
            elif payment.total_amount_to_pay - payment.total_amount_paid != 0:
                payment.payment_status = "IN PROGRESS"

            if refund_transaction is not None:
                payment.transaction_to_refund = refund_transaction
            payment.save()   
        return True, "payment has been to applied to installments successfully"        
    except Exception as e:
        print(f"\n\nError: {str(e)}\n\n")
        return False, f"[Error]: {str(e)}"


def record_payment_transaction(data:dict, base_domain: str):
    """
    This function is for applying payment to installments
    data
    """
    transaction = None
    contract_id = None
    try:
        installment = data.get("installment")
        payment_date = data.get("payment_date")
        payment_amount = data.get("payment_amount")
        payment_proof = data.get("document")
        installment = ContractPaymentInstallment.objects.filter(id=installment).select_related("contract_payment").first()
        if installment is None:
            raise ContractPaymentInstallment.DoesNotExist
        
        transaction = PaymentInstallmentTransaction(
            installment=installment,
            payment_date=payment_date,
            payment_amount=payment_amount,
            payment_proof=payment_proof
        )
        transaction.save()
        transaction.payment_proof_url = f"{base_domain}/{transaction.payment_proof.url.lstrip('/')}"
        transaction.save()

        succeed, message = clear_installment_and_payment(transaction=transaction, installment=installment)
        contract_id = installment.contract_payment.contract.id
        return succeed, message, contract_id
    except Exception as e:
        print("\nError: ", str(e), "\n")
        return False, f"[Error]: {str(e)}", contract_id




    

