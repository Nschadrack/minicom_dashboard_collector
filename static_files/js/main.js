window.onload=function(){
    var car_title_header_button_clicked = document.getElementById("car_title_header_and_new_btn_button");
    // var cancelOperation = document.getElementById("cancel_operation");
    var groupCarRegisterForm = document.getElementsByClassName("car_new_form");

    /* Group car page function call */
    car_title_header_button_clicked.addEventListener('click', showNewGroupCarRegiseterForm);
    // cancelOperation.addEventListener('click', showGroupCarList);
}

/* javascript for group car page */
function showNewGroupCarRegiseterForm(e){
    var form_div_to_shows = document.getElementsByClassName("car_new_form_div");
    var car_list_to_hide = document.getElementById("car_table_data");
    var car_title_header_button_clicked = document.getElementById("car_title_header_and_new_btn_button");
    var car_title_header_paragraph = document.getElementById("car_title_header_and_new_btn_p");

    Array.from(form_div_to_shows).forEach((form_div_to_show) =>{
        form_div_to_show.style.display="block";
    });
    car_list_to_hide.style.display = "none";
    car_title_header_button_clicked.style.display="none";
    car_title_header_paragraph.style.display="none";
}
function hideNewGroupCarRegiseterForm(e){
    var form_div_to_shows = document.getElementsByClassName("car_new_form_div");
    var car_list_to_hide = document.getElementById("car_table_data");
    var car_title_header_button_clicked = document.getElementById("car_title_header_and_new_btn_button");
    var car_title_header_paragraph = document.getElementById("car_title_header_and_new_btn_p");

    var assignmentTables = document.getElementsByClassName("new-assignment");
    var upperDivs = document.getElementsByClassName("upper-detail-div");

    // Convert HTMLCollection to an array before using forEach
    if(upperDivs != null){
        Array.from(upperDivs).forEach((upperDiv) => {
            upperDiv.style.display = "block";
        });
    }

    if(assignmentTables != null){
        Array.from(assignmentTables).forEach((assignmentTable) => {
            assignmentTable.style.display = "none";
        });
    }

    Array.from(form_div_to_shows).forEach((form_div_to_show) =>{
        form_div_to_show.style.display="none";
    });

    if(car_list_to_hide != null){
        car_list_to_hide.style.display = "block";
    }
    if(car_title_header_button_clicked != null){
        car_title_header_button_clicked.style.display="block";
    }
    if(car_title_header_paragraph != null){
        car_title_header_paragraph.style.display="block";
    }
    
}

function showUserRegistrationForm(e){
    var user_login_form = document.getElementById("login-form");
    var user_register_form = document.getElementById("registration-form");

    user_login_form.style.display="none";
    user_register_form.style.display = "block";
}
function showUserLoginForm(e){
    var user_login_form = document.getElementById("login-form");
    var user_register_form = document.getElementById("registration-form");

    user_login_form.style.display="block";
    user_register_form.style.display = "none";
}
function toggleAssetRegistrySection(e){
    var assets_registry_section = document.getElementById("assets-registry-section");
    var style = window.getComputedStyle(assets_registry_section);
    var displayCss = style.getPropertyValue("display")
    if (displayCss === "none"){
        assets_registry_section.style.display = "block";
    }else{
        assets_registry_section.style.display = "none";
    }
    
}

function toggleAssetsConsolidationSection(e){
    var assets_consolidation_section = document.getElementById("assets-consolidation-section");
    var style = window.getComputedStyle(assets_consolidation_section);
    var displayCss = style.getPropertyValue("display")
    if (displayCss === "none"){
        assets_consolidation_section.style.display = "block";
    }else{
        assets_consolidation_section.style.display = "none";
    }
}

function toggleUsersManagementAssetSection(e){
    var users_management_section = document.getElementById("users-management-section");
    var style = window.getComputedStyle(users_management_section);
    var displayCss = style.getPropertyValue("display")
    if (displayCss === "none"){
        users_management_section.style.display = "block";
    }else{
        users_management_section.style.display = "none";
    }
}

function showSparepartsWindows(e){
    var sparepartaddButton = document.getElementById("add-sparepart-button");
    var sparepartWindow = document.getElementById("spareparts_div");
    sparepartWindow.style.display = "block";
}
function hideSparepartsWindows(e){
    var sparepartaddButton = document.getElementById("add-sparepart-button");
    var sparepartWindow = document.getElementById("spareparts_div");
    sparepartWindow.style.display = "none";
}

function fillSparepartSelectBox(e){
    var spareparts = document.getElementById("spareparts");
    var selectedSparepart = document.getElementById("partnumber").value;
    spareparts.style.display = "block";
    spareparts.innerHTML += `<option value="${selectedSparepart}" selected>${selectedSparepart}</option>`;    
}
function toggleNavigations(e){
    var navigationDiv = document.getElementById("aside_navigation");
    var mainLoadDiv = document.getElementById("main_load");
    var mainLoadHeader = document.getElementById("main_load_header");
    var styleNav = window.getComputedStyle(navigationDiv);
    var displayCssNav = styleNav.getPropertyValue("display")

    if (displayCssNav === "none"){
        navigationDiv.style.display = "block";
        navigationDiv.style.width = "20%";
        mainLoadDiv.style.width = "80%";
        mainLoadHeader.style.left = "20%";
    }else{
        navigationDiv.style.display = "none";
        mainLoadDiv.style.width = "100%";
        mainLoadHeader.style.left = "0px";
    }

}

function showAssignmentTable(value){
    var assignmentTables = document.getElementsByClassName("new-assignment");
    var upperDivs = document.getElementsByClassName("upper-detail-div");

    // Convert HTMLCollection to an array before using forEach
    Array.from(upperDivs).forEach((upperDiv) => {
        upperDiv.style.display = value === "block" ? "none" : "block";
    });

    Array.from(assignmentTables).forEach((assignmentTable) => {
        assignmentTable.style.display = value;
    });
}

function generateReport() {
//   var pdf = new jsPDF('p', 'pt', 'letter');
var pdf = new jsPDF();
//   var reportContent = document.getElementById("content-report")
//   pdf.canvas.height = 72 * 11;
//   pdf.canvas.width = 72 * 8.5;

//   pdf.autoTable(reportContent);
  /*content-report */
  pdf.autoTable({ html: '#content-report' })
  pdf.save('table.pdf')

//   pdf.save('test.pdf');
}

// function generateReport()
//   {
//     var reportContent = document.getElementById("content-report");
//     html2canvas(reportContent,{
//     onrendered:function(canvas){
//     var pdf = new jsPDF('p', 'pt', 'letter');
//     pdf.canvas.height = 72 * 11;
//     pdf.canvas.width = 72 * 8.5;
//     pdf.fromHTML(reportContent);

//     pdf.save('test.pdf');
//    }

//    });

//   }

// Tabs
document.addEventListener("DOMContentLoaded", function() {
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');

    tabLinks.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // Remove active class from all tabs and contents
            tabLinks.forEach(tab => tab.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to the clicked tab and corresponding content
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
});

