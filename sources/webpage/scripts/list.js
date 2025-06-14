const pageSize = 10;
let currentPage = 1;
let totalPages = 1;

async function fetchData(page) {
    console.log('fetchData')

    $('#loading-spinner').show();
    $('#table-body').empty();

    try {
        const response = await fetch(`https://61yfnkfn3i.execute-api.eu-west-3.amazonaws.com/diagnostics?page=${page}&pageSize=${pageSize}`);            
        const text = await response.text();
        const result = JSON.parse(text);

        console.log(result);

        document.getElementById('total-records').textContent = `Total registros: ${result.total}`;

        state.querySet = result.data;
        totalPages = Math.ceil(result.total / pageSize);

        buildTable();
    } catch (error) {
        console.error('Error al cargar los datos:', error);
        $('#table-body').append('<tr><td colspan="3">Error al cargar los datos</td></tr>');
    } finally {
        $('#loading-spinner').hide(); // Ocultar spinner
    } 
}

var state = {
    'querySet': [],
    'page': 1,
    'rows': 10,
    'window': 5,
}

fetchData(currentPage);

function pagination(querySet, page, rows) {            
    console.log('pagination');
    console.log('querySet: ' + querySet);

    return {
        'querySet': querySet,
        'pages': totalPages,
    }
}

function pageButtons(pages) {
    var wrapper = document.getElementById('pagination-wrapper');

    wrapper.innerHTML = ``;
    console.log('Pages:', pages);

    var maxLeft = (state.page - Math.floor(state.window / 2));
    var maxRight = (state.page + Math.floor(state.window / 2));

    if (maxLeft < 1) {
        maxLeft = 1;
        maxRight = state.window;
    }

    if (maxRight > pages) {
        maxLeft = pages - (state.window - 1);

        if (maxLeft < 1) {
            maxLeft = 1;
        }
        maxRight = pages;
    }

    for (var page = maxLeft; page <= maxRight; page++) {
        wrapper.innerHTML += `<button value=${page} class="page btn btn-sm btn-outline-info">${page}</button>`;
    }

    if (state.page != 1) {
        wrapper.innerHTML = `<button value=${1} class="page btn btn-sm btn-info">&#171; First</button>` + wrapper.innerHTML;
    }

    if (state.page != pages) {
        wrapper.innerHTML += `<button value=${pages} class="page btn btn-sm btn-info">Last &#187;</button>`;
    }

    $('.page').on('click', function () {
        $('#table-body').empty();
        state.page = Number($(this).val());
        fetchData(state.page);
    });
}

function buildTable() {
    var table = $('#table-body');

    var data = pagination(state.querySet, state.page, state.rows);
    var myList = data.querySet;

    console.log(myList);

    for (var i in myList) {
        var row = `<tr>
                    <td>${myList[i].numRegistro}</td>
                    <td>${myList[i].edad}</td>
                    <td>${myList[i].sexoNombre}</td>
                    </tr>`;
        table.append(row);
    }

    pageButtons(data.pages);
}