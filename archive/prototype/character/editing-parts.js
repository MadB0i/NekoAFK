// Editing-only cutout registration. Source pixels stay in the approved image.
// SVG paths are extraction masks, not replacement illustration or drawn anatomy.
(() => {
  const parts=[
    {id:'base',parent:null,pivot:[570,847],label:'Pelvis / seated base',d:'M381 678 Q462 637 595 699 L880 734 Q960 775 967 844 L956 912 Q759 961 546 905 L419 880 Z'},
    {id:'tail',parent:null,pivot:[353,758],label:'Tail root',d:'M369 595 C291 554 170 610 116 675 C51 750 25 846 89 904 C154 969 250 959 330 886 L371 791 Z'},
    {id:'hair-back',parent:'torso',pivot:[477,310],label:'Back hair',d:'M490 175 C429 187 388 252 350 300 C305 344 278 380 288 429 L303 463 C268 494 200 528 153 501 C191 537 219 551 251 541 C194 587 177 626 225 695 L305 787 L406 810 L414 700 L403 558 L398 410 L479 341 Z M725 267 Q767 313 789 382 Q831 413 830 442 Q892 460 899 522 Q936 561 957 626 L975 671 L905 657 L836 558 L758 424 L697 344 Z'},
    {id:'torso',parent:'base',pivot:[491,747],label:'Torso / hip support',d:'M357 312 Q438 322 489 294 L546 323 L624 365 Q657 368 689 355 L759 371 L787 424 L722 472 L660 535 L625 613 L555 683 L444 724 L357 681 L328 587 L302 474 L295 363 Z'},
    {id:'upper-leg',parent:'base',pivot:[485,834],label:'Upper leg / hip',d:'M453 838 Q451 733 558 633 L731 527 Q780 476 820 503 L851 548 L809 626 L734 701 L659 805 L576 871 Z'},
    {id:'lower-leg',parent:'upper-leg',pivot:[797,542],label:'Lower leg / KNEE',d:'M730 530 Q785 487 827 510 Q850 533 854 579 L879 652 Q902 713 921 770 L925 798 L876 842 L875 871 L880 904 L891 943 Q902 959 900 979 L913 1003 L929 1046 L809 1046 L814 1017 L813 1000 L810 979 L812 962 L805 942 L796 921 L790 902 L787 881 L781 863 L778 850 L749 863 Q725 884 711 854 L698 815 Q687 799 697 770 L705 741 Q674 740 664 711 Q651 686 665 643 L687 589 Z'},
    {id:'foot',parent:'lower-leg',pivot:[860,1042],label:'Swing foot / ankle',d:'M806 1010 Q852 995 910 1010 L962 1080 L1030 1140 L1004 1200 L931 1196 Q898 1194 881 1178 Q868 1162 860 1134 L853 1120 L835 1111 Q808 1109 793 1097 Q788 1083 800 1054 Z'},
    {id:'second-foot',parent:'base',pivot:[608,871],label:'Resting foot / ankle',d:'M617 835 Q585 829 550 841 L469 838 Q417 836 398 853 L370 896 Q363 919 382 931 L416 917 L475 908 L550 920 L611 914 L625 877 Z'},
    {id:'head',parent:'torso',pivot:[579,351],label:'Head / neck',d:'M421 203 Q449 164 493 133 Q534 108 567 81 L637 4 L672 104 Q708 114 724 142 L811 153 L763 212 Q752 242 746 275 Q736 310 709 331 L660 371 L607 391 L563 365 L523 327 Q481 324 458 280 L454 248 Z'},
    {id:'ear-left',parent:'head',pivot:[616,124],label:'Screen-left ear',d:'M550 110 Q578 52 637 4 Q658 49 671 110 L639 126 L601 128 Z'},
    {id:'ear-right',parent:'head',pivot:[732,182],label:'Screen-right ear',d:'M709 139 Q751 140 811 153 L778 180 L749 221 L727 203 Z'},
    {id:'hair-front',parent:'head',pivot:[633,151],label:'Front fringe',d:'M459 210 Q485 152 565 125 L630 112 Q696 119 714 165 L734 232 L720 286 L690 312 L706 257 L695 211 L661 184 Q608 225 567 228 L536 218 L528 266 L517 284 L507 239 L480 229 Z'},
    {id:'hair-tips',parent:'head',pivot:[552,313],label:'Front hair tips',d:'M529 276 Q534 317 550 346 L559 382 L590 439 L590 487 L608 526 L578 509 L559 474 L549 403 L524 362 L510 326 Z M692 301 L722 317 Q758 365 774 394 L760 432 L724 415 L696 369 L675 345 Z'},
    {id:'phone-hand',parent:'torso',pivot:[692,488],label:'Phone hand / wrist',d:'M683 453 L725 439 L767 424 L787 386 Q797 377 818 381 L874 388 L881 399 L851 446 L835 480 L784 492 L740 507 L710 520 L691 502 Z'},
    {id:'thumb',parent:'phone-hand',pivot:[727,468],label:'Scrolling thumb',d:'M698 462 Q713 449 738 439 L760 429 Q770 430 772 437 L760 447 L737 459 L724 476 L707 481 Z'},
    {id:'mouth',parent:'head',pivot:[596,303],label:'Mouth',d:'M575 284 L616 302 L612 320 L573 302 Z'},
    {id:'eyes',parent:'head',pivot:[617,255],label:'Eyes / blink',d:'M553 212 Q580 205 609 240 L602 262 Q569 251 550 229 Z M626 251 Q658 248 678 274 L664 295 Q639 288 621 272 Z'},
  ];
  // These occlusions come from the original pose: close parts cover far parts.
  const order=['tail','hair-back','base','torso','upper-leg','lower-leg','foot','second-foot','head','ear-left','ear-right','hair-front','hair-tips','phone-hand','thumb','mouth','eyes'];
  const chairFront='M236 743 Q231 726 249 720 Q326 704 403 721 Q431 727 440 748 L440 765 L365 776 L377 1007 Q376 1033 357 1035 L328 1035 Q316 1032 316 1017 L311 783 L256 780 Q239 777 236 763 Z';
  window.NekoEditingParts={canvas:[1138,1382],registration:[-5,65],parts,order,chairFront,clip:{name:'editing / phone-scroll',duration:24}};
})();
