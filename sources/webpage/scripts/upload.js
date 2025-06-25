var region = "eu-west-3";
var accessKeyId = "AKIAQVIGH346E5IYBCME";
var secretAccessKey = "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";

AWS.config.update({
  region: region,
  credentials: new AWS.Credentials(accessKeyId, secretAccessKey),
});

var s3 = new AWS.S3();

function formatDate(lastModified) {
  const date = new Date(lastModified);
  return date.toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function refreshFileList(bucketname) {
  var tableBody = document.querySelector("#fileTable tbody");
  tableBody.innerHTML = "";

  s3.listObjectsV2({ Bucket: bucketname }, (err, data) => {
    if (err) {
      console.log("Error fetching file list ", err);
    } else {
      console.log(data);
      data.Contents.forEach((object) => {
        var fileRow = document.createElement("tr");
        var fileNameCell = document.createElement("td");
        fileNameCell.textContent = object.Key;
        fileRow.appendChild(fileNameCell);

        var fileSizeCell = document.createElement("td");
        fileSizeCell.textContent = object.Size;
        fileRow.appendChild(fileSizeCell);

        var fileDateCell = document.createElement("td");
        fileDateCell.textContent = formatDate(object.LastModified);
        fileRow.appendChild(fileDateCell);

        var deleteCell = document.createElement("td");
        var deleteButton = document.createElement("button");
        deleteButton.textContent = "Eliminar";
        deleteButton.addEventListener("click", () => {
          deleteFile(bucketname, object.Key);
        });
        deleteCell.appendChild(deleteButton);
        fileRow.appendChild(deleteCell);

        tableBody.appendChild(fileRow);
      });
    }
  });
}

let pendingDelete = { bucketname: "", key: "" };

function deleteFile(bucketname, key) {
  pendingDelete = { bucketname, key };
  $("#confirmDeleteModal").modal("show"); // Mostrar modal con jQuery
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("confirmDeleteBtn").addEventListener("click", () => {
    const { bucketname, key } = pendingDelete;
    const params = { Bucket: bucketname, Key: key };

    s3.deleteObject(params, (err, data) => {
      if (err) {
        console.error("Error al eliminar el archivo:", err);
      } else {
        console.log("Archivo eliminado correctamente");
        refreshFileList(bucketname);
      }
    });

    $("#confirmDeleteModal").modal("hide"); // Ocultar modal con jQuery
  });
});

function uploadFile(bucketname) {
  let files = document.getElementById("fileInput").files;

  var fileCount = files.length;

  for (var i = 0; i < fileCount; i++) {
    var file = files[i];
    var params = {
      Bucket: bucketname,
      Key: file.name,
      Body: file,
      ContentType: file.type,
    };

    s3.upload(params, (err, data) => {
      if (err) {
        console.error("Error: ", err);
      } else {
        console.log("File uploaded successfully: ", data.Location);
        refreshFileList(bucketname);
      }
    });
  }
}

refreshFileList("tfm-store");
