import axios from 'axios';
import JSONEditor from 'jsoneditor';
import 'jsoneditor/dist/jsoneditor.min.css';

interface IPhi {
  attr: string;
  op: string;
  val: string;
}

function createBlock(phi: String, counter: number): HTMLElement {
  const wrapper = document.createElement('div');
  wrapper.classList.add('row', 'dynamic-block');

  const columns = [
    {
      type: 'text',
      idPrefix: 'attr',
      className: 'form-control',
    },
    {
      type: 'select',
      idPrefix: 'op',
      className: 'form-select',
    },
    {
      type: 'text',
      idPrefix: 'val',
      className: 'form-control',
    }
  ];

  columns.forEach((col) => {
    const colDiv = document.createElement('div');
    colDiv.classList.add(`col-4`); 

    if (col.type === 'select') {
      const select = document.createElement('select');
      select.id = `${col.idPrefix}${phi}${counter}`;
      select.className = col.className;

      if (col.idPrefix === 'op') {
        const eqOption = document.createElement('option');
        eqOption.value = '=';
        eqOption.textContent = '=';
        select.appendChild(eqOption);

        const disOption = document.createElement('option');
        disOption.value = '!=';
        disOption.textContent = '!=';
        select.appendChild(disOption);

        const lessOption = document.createElement('option');
        lessOption.value = '<';
        lessOption.textContent = '<';
        select.appendChild(lessOption);

        const leqOption = document.createElement('option');
        leqOption.value = '<=';
        leqOption.textContent = '<=';
        select.appendChild(leqOption);

        const majOption = document.createElement('option');
        majOption.value = '>';
        majOption.textContent = '>';
        select.appendChild(majOption);

        const maqOption = document.createElement('option');
        maqOption.value = '>=';
        maqOption.textContent = '>=';
        select.appendChild(maqOption);
      }

      colDiv.appendChild(select);
    } else {
      const input = document.createElement('input');
      input.type = col.type;
      input.id = `${col.idPrefix}${phi}${counter}`;
      input.className = col.className;
      colDiv.appendChild(input);
    }

    wrapper.appendChild(colDiv);
  });

  return wrapper;
}


// on body loaded
document.addEventListener("DOMContentLoaded", () => {
  const selectFp = document.getElementById("fp") as HTMLSelectElement;
  const buttonAddPsi = document.getElementById("addPsi") as HTMLButtonElement;
  const buttonRemPsi = document.getElementById("remPsi") as HTMLButtonElement;
  const divPsi = document.getElementById(`psi`) as HTMLDivElement;
  const divEpb = document.getElementById("epb") as HTMLDivElement;
  const spinnerContainer = document.querySelector('.spinner-container') as HTMLDivElement;
  const divM = document.getElementById('jsoneditorM') as HTMLElement;
  const divNM = document.getElementById('jsoneditorNM') as HTMLElement;
  const options = {};
  const jsonM = new JSONEditor(divM, options);
  const jsonNM = new JSONEditor(divNM, options);

  const formLog = document.getElementById('logForm') as HTMLElement;
  formLog.addEventListener('submit', event => {
    event.preventDefault()
    const fileInput = document.getElementById("logInput") as HTMLInputElement;
    const file = fileInput.files?.[0]; if (!file) { alert('Please select a file to upload'); return; }

    const formData = new FormData();
    formData.append('file', file);

    axios.post('http://127.0.0.1:8000/api/uploadLog', formData, { headers: { 'Content-Type': 'multipart/form-data' } }
    ).then(response => {
      initLog(response)
      // console.log('File uploaded successfully:', response.data);
    }).catch(error => {
      console.error('Error uploading file:', error);
    });
  });

  // Function to update Psi button state
  const updatePsiAndPatternB = () => {
    if ((selectFp.value != "occurs") && (selectFp.value != "absent")) {
      buttonAddPsi.disabled = false;
      buttonRemPsi.disabled = false;
      const psiInput: NodeListOf<HTMLInputElement> = divPsi.querySelectorAll(".dynamic-psi");
      psiInput.forEach(function (psi) {
        psi.disabled = false
      });
      divEpb.style.display = ""; // Show the div
    } else {
      buttonAddPsi.disabled = true;
      buttonRemPsi.disabled = true;
      const psiInput: NodeListOf<HTMLInputElement> = divPsi.querySelectorAll(".dynamic-psi");
      psiInput.forEach(function (psi) {
        psi.disabled = true
      });
      divEpb.style.display = "none"; // Hide the div
    }
  };

  // Add event listener to the FP select element
  selectFp.addEventListener("change", updatePsiAndPatternB);

  // Initialize the button state
  updatePsiAndPatternB();

  const listItems: NodeListOf<HTMLElement> = document.querySelectorAll("ul li"); 
  listItems.forEach(function (item) {
    item.onclick = function () {
      const log = (this as HTMLDivElement).innerText; // this returns clicked li's value
      axios.post('http://127.0.0.1:8000/api/loadLog', { name: log })
        .then(response => {
          initLog(response);
          //console.log(response.data)
        })
        .catch(error => console.error('Error fetching data:', error));
    }
  });

  // Event listeners for the Phi buttons, both events and objects
  const listPhi: Array<String> = ["EA", "OA", "EB", "OB"];
  listPhi.forEach(function (item) {
    const container = document.getElementById(`phi${item}`);
    if (container) {
      document.getElementById(`addPhi${item}`)?.addEventListener('click', () => {
        const divsRow: NodeListOf<HTMLDivElement> = container.querySelectorAll('.dynamic-block');
        const counter = divsRow.length
        const newBlock = createBlock(item, counter);
        container.appendChild(newBlock);
      });
      document.getElementById(`remPhi${item}`)?.addEventListener('click', () => {
        const lastBlock = container.querySelector('.dynamic-block:last-child'); // Select the last dynamic block of phi
        if (lastBlock) {
          container.removeChild(lastBlock); // Remove the last block
        }
      });
    }
  });


  // Event listeners for the Psi buttons
  buttonAddPsi.addEventListener('click', () => {
    const nPsi = divPsi.querySelectorAll('.dynamic-psi');
    const newBlock = document.createElement('input');
    newBlock.type = "text";
    newBlock.classList.add('form-control', 'dynamic-psi');
    newBlock.id = `psi${nPsi.length + 1}`
    divPsi.appendChild(newBlock);
  });
  buttonRemPsi.addEventListener('click', () => {
    const lastBlock = divPsi.querySelector('.dynamic-psi:last-child'); // Select the last dynamic psi
    if (lastBlock) {
      divPsi.removeChild(lastBlock); // Remove the last block
    }
  });

  function showSpinner() {
    spinnerContainer.style.display = 'flex';
  }

  function hideSpinner() {
    spinnerContainer.style.display = 'none';
  }

  const downloadM = document.getElementById('downloadLinkM') as HTMLLinkElement;
  const downloadNM = document.getElementById('downloadLinkNM') as HTMLLinkElement;

  const formOCCR = document.getElementById('submitOCCR') as HTMLElement;
  formOCCR.addEventListener('submit', event => {
    event.preventDefault();
    showSpinner();
    console.log("Applying OCCR to object-centrice event log...");
    //-------------- retrieve Event Pattern A values -------------------------------
    const etA: string = (document.getElementById("etA") as HTMLSelectElement).value;
    const rowsPhiEA = (document.getElementById("phiEA") as HTMLElement).querySelectorAll('.dynamic-block')
    const phietA: { [id: number] : IPhi; } = {};
    let i = 0
    rowsPhiEA.forEach( () => {
      const attr = (document.getElementById(`attrEA${i}`) as HTMLInputElement).value;
      const op = (document.getElementById(`opEA${i}`) as HTMLSelectElement).value;
      const val = (document.getElementById(`valEA${i}`) as HTMLInputElement).value;
      
      phietA[i] = {attr: attr, op: op, val: val}
      i = i + 1
    })
    const opA: string = (document.getElementById("opA") as HTMLSelectElement).value;
    const nA: number = Number((document.getElementById("nA") as HTMLInputElement).value);
    const qA: string = (document.getElementById("qA") as HTMLInputElement).value;
    const otA: string = (document.getElementById("otA") as HTMLSelectElement).value;
    const rowsPhiOA = (document.getElementById("phiOA") as HTMLElement).querySelectorAll('.dynamic-block')
    const phiotA: { [id: number] : IPhi; } = {};
    i = 0
    rowsPhiOA.forEach( () => {
      const attr = (document.getElementById(`attrOA${i}`) as HTMLInputElement).value;
      const op = (document.getElementById(`opOA${i}`) as HTMLSelectElement).value;
      const val = (document.getElementById(`valOA${i}`) as HTMLInputElement).value;
      
      phiotA[i] = {attr: attr, op: op, val: val}
      i = i + 1
    })
     
    const EA: any = {
      et: etA,
      phiet: phietA,
      op: opA,
      n: nA,
      q: qA,
      ot: otA,
      phiot: phiotA
    }
    //-------------- retrieve FP -------------------------------
    const fp: string = (document.getElementById("fp") as HTMLSelectElement).value;
    //-------------- eventually retrieve delta and Instance Link -------------------------------
    const opD: string = (document.getElementById("opD") as HTMLSelectElement).value;
    const td: number = Number((document.getElementById("td") as HTMLInputElement).value);
    const psi: Array<string> = [];
    const nPsi: NodeListOf<HTMLInputElement> = divPsi.querySelectorAll('.dynamic-psi');
    nPsi.forEach(function (p) {
      psi.push(p.value)
    });
    const FP: any = {
      fp: fp,
      opD: opD,
      td: td,
      psi: psi
    }
    //-------------- eventually retrieve Event Pattern B values -------------------------------
    const etB: string = (document.getElementById("etB") as HTMLSelectElement).value;
    const rowsPhiEB = (document.getElementById("phiEB") as HTMLElement).querySelectorAll('.dynamic-block')
    const phietB: { [id: number] : IPhi; } = {};
    i = 0
    rowsPhiEB.forEach( () => {
      const attr = (document.getElementById(`attrEB${i}`) as HTMLInputElement).value;
      const op = (document.getElementById(`opEB${i}`) as HTMLSelectElement).value;
      const val = (document.getElementById(`valEB${i}`) as HTMLInputElement).value;
      
      phietB[i] = {attr: attr, op: op, val: val}
      i = i + 1
    })
    const opB: string = (document.getElementById("opB") as HTMLSelectElement).value;
    const nB: number = Number((document.getElementById("nB") as HTMLInputElement).value);
    const qB: string = (document.getElementById("qB") as HTMLInputElement).value;
    const otB: string = (document.getElementById("otB") as HTMLSelectElement).value;
    const rowsPhiOB = (document.getElementById("phiOB") as HTMLElement).querySelectorAll('.dynamic-block')
    const phiotB: { [id: number] : IPhi; } = {};
    i = 0
    rowsPhiOB.forEach( () => {
      const attr = (document.getElementById(`attrOB${i}`) as HTMLInputElement).value;
      const op = (document.getElementById(`opOB${i}`) as HTMLSelectElement).value;
      const val = (document.getElementById(`valOB${i}`) as HTMLInputElement).value;
      
      phiotB[i] = {attr: attr, op: op, val: val}
      i = i + 1
    })
    const EB: any = {
      et: etB,
      phiet: phietB,
      op: opB,
      n: nB,
      q: qB,
      ot: otB,
      phiot: phiotB
    }
    console.log(EA)
    console.log(FP)
    console.log(EB)
    if (FP.fp == "occurs" || FP.fp == "absent") {
      axios.post('http://127.0.0.1:8000/api/evalOCCRu', { ePa: EA, fp: FP })
        .then(response => {
          console.log(response.status)
          const m = response.data.matching;
          const nm = response.data.nonmatching;

          const urlM = window.URL.createObjectURL(new Blob([JSON.stringify(m)]));
          downloadM.href = urlM;
          downloadM.setAttribute('download', 'matching_set.json');

          const urlNM = window.URL.createObjectURL(new Blob([JSON.stringify(nm)]));
          downloadNM.href = urlNM;
          downloadNM.setAttribute('download', 'non-matching_set.json');

          jsonM.set(Object.fromEntries(Object.entries(m).slice(0, 20)));
          jsonNM.set(Object.fromEntries(Object.entries(nm).slice(0, 20)));
        })
        .catch(error => console.error('Error submitting data:', error))
        .finally(() => {
          hideSpinner();
        });
    } else {
      axios.post('http://127.0.0.1:8000/api/evalOCCRb', { ePa: EA, fp: FP, ePb: EB })
        .then(response => {
          console.log(response.status)
          const m = response.data.matching;
          const nm = response.data.nonmatching;

          const urlM = window.URL.createObjectURL(new Blob([JSON.stringify(m)]));
          downloadM.href = urlM;
          downloadM.setAttribute('download', 'matching_set.json');

          const urlNM = window.URL.createObjectURL(new Blob([JSON.stringify(nm)]));
          downloadNM.href = urlNM;
          downloadNM.setAttribute('download', 'non-matching_set.json');

          jsonM.set(Object.fromEntries(Object.entries(m).slice(0, 20)));
          jsonNM.set(Object.fromEntries(Object.entries(nm).slice(0, 20)));
        })
        .catch(error => console.error('Error submitting data:', error))
        .finally(() => {
          hideSpinner();
        });
    }
  });

  // ------------- end DOMContentLoaded --------------------
});

function initLog(response: axios.AxiosResponse<any, any>) {
  (document.getElementById('logLoaded') as HTMLDivElement).innerText = response.data.logName;
  (document.getElementById('eventsLoaded') as HTMLDivElement).innerText = response.data.numEvents;
  (document.getElementById('objectsLoaded') as HTMLDivElement).innerText = response.data.numObjects;
  var selectorEtA: HTMLElement | null = document.getElementById("etA");
  var selectorEtB: HTMLElement | null = document.getElementById("etB");
  if ((selectorEtA != null) && (selectorEtB != null)) {
    emptySelect(selectorEtA);
    emptySelect(selectorEtB);
    response.data.evTypes.forEach((et: string) => {
      var newoption1 = document.createElement("option");
      newoption1.text = et;
      newoption1.value = et;
      (selectorEtA as HTMLSelectElement).add(newoption1);
      var newoption2 = document.createElement("option");
      newoption2.text = et;
      newoption2.value = et;
      (selectorEtB as HTMLSelectElement).add(newoption2);
    });
  }
  var selectorOtA: HTMLElement | null = document.getElementById("otA");
  var selectorOtB: HTMLElement | null = document.getElementById("otB");
  if ((selectorOtA != null) && (selectorOtB != null)) {
    emptySelect(selectorOtA);
    emptySelect(selectorOtB);
    response.data.objTypes.forEach((ot: string) => {
      var newoption = document.createElement("option");
      newoption.text = ot;
      newoption.value = ot;
      (selectorOtA as HTMLSelectElement).add(newoption);
      var newoption2 = document.createElement("option");
      newoption2.text = ot;
      newoption2.value = ot;
      (selectorOtB as HTMLSelectElement).add(newoption2);
    });
  }
}
function emptySelect(selector: HTMLElement) {
  while ((selector as HTMLSelectElement).options.length > 0) {
    (selector as HTMLSelectElement).remove(0);
  }
}

