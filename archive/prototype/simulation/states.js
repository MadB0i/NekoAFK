// Development fixtures only. No agent transport, subscriptions or backend.
window.NekoSimulation={
  editing:{state:'editing',label:'EDITING',tasks:7,total:11,failures:0,confidence:64,level:'MEDIUM',lines:['Editing components/*.tsx','3 files · +84 −12','Diagnostics clean']},
  testing:{state:'testing',label:'TESTING',tasks:7,total:11,failures:0,confidence:72,level:'MEDIUM',lines:['Running 41 tests','18 passed · verification running','Watching agent activity']},
  failed:{state:'failed',label:'FAILED',tasks:7,total:11,failures:1,confidence:58,level:'LOW',lines:['verify.test.ts failed','Last exit: 1','Waiting for a correction']},
  frustrated:{state:'frustrated',label:'FRUSTRATED',tasks:7,total:11,failures:3,confidence:41,level:'LOW',lines:['Same test failed three times','Last exit: 1','Repeated failure, stronger reaction']},
  verifying:{state:'verifying',label:'VERIFYING',tasks:10,total:11,failures:0,confidence:null,level:'CHECKING',lines:['Agent claims completion','Independent verification running','Celebration held until verified']},
  success:{state:'success',label:'VERIFIED',tasks:11,total:11,failures:0,confidence:100,level:'VERIFIED',lines:['All 41 tests passed','11 / 11 tasks completed','Completion verified']},
};
