

Check for updates 

# Sparse deconvolution improves the resolution of  live-cell super-resolution fluorescence microscopy 

Weisonghao18,Shiqunhao218,Liuju Li18aoshuaiHuangShijia Xing2Yulin ng2,Guohua Qiu1, Zhenqian Han', Yingxu Shang4, De-en Sun⊙5,Chunyan Shan6, Runlong Wu2,LushengGu7,Sn ang7, RngCn, Jan X,Ynqn Mo, Jianng ng,i Ji7Xingg4u Jian Liu1,14,Haoyu Li and Liangyi Chen 2,16,17

Amain determinant of the spatial resolution of live-cell super-resolution (SR) microscopes is the maximum photon flux that can be collected. To further increase the effective resolution for a given photon flux, we take advantage of a priori knowledge about the sparsity and continuity of biological structures to develop a deconvolution algorithm that increases the resolution of SR microscopes nearly twofold. Our method, sparse structured illumination microscopy (Sparse-SiM), achieves ~60-nm resolution at a frame rate of up to 54 Hz, allowing it to resolve intricate structures, including small vesicular fusion pores, ring-shaped nuclear pores formed by nucleoporins and relative movements of inner and outer mitochondrial membranes in live cells. Sarse deconvolution can also be used to increase the three-dimensional resolution of spinning-disc confocal-based SIM, even at low signal-to-noise ratios, which allows four-color, three-dimensional live-cell SR imaging at ~90-nm resolution. Overall, sparse deconvolution will be useful to increase the spatiotemporal resolution of live-cell fluorescence microscopy.

espite theoretically unlimited resolution, the spatial resolution of SR microscopy in live-cell imaging is still limited.Due to motion artifacts of fast-moving subcellular structures in live cells, such as tubular endoplasmic reticulum (ER)1, lipid droplets, mitochondria and lysosomes2, any increase in the spatial resolution must be matched with an increase in temporal resolution.Therefore, the highest resolution of current live-SR microscopy is limited to ~60 nm, irrespective of the modalities used7.To achieve that resolution, excessive illumination power (kW-MW mm-2) and long exposures (>2 s) are usually required, which may compromise the integrity of the holistic fluorescent structure and degrade the achievable resolution.



Previously we developed a Hessian deconvolution algorithm for SIM, which enables ultrafast and hour-long SR imaging in live cells.However, its resolution is limited at 90-110nm posed by linear spatial frequency mixing. Nonlinear SIM with ~60-nm resolution comes at a cost of reduced temporal resolution and requires photoactivatable/photoswitchable fluorescent proteins that are susceptible to photobleaching10. Because the resolution and contrast inside deep layers of the cell are still compromised by fluorescence emissions and the scattering from out-of-focus planes,high-contrast SR-SIM imaging is largely limited to imaging depths of 0.1 to 1m (refs. 9-11). To date, no SR method has achieved millisecond exposures with ~60-nm spatiotemporal resolution in live cells or is capable of multicolor, three-dimensional (3D)long-term SR imaging.



Alternatively, mathematical bandwidth extrapolation that may boost SR without hardware modifications was first proposed in the 1960s (refs. 12,13).It follows that when the object being imaged has a finite size, there exists a unique analytic function that coincides inside the bandwidth-limited frequency spectrum band of the optical transfer function (OTF), thus enabling reconstruction of the complete object by extrapolating the observed spectrum 14-16For example, the iterative Richardson-Lucy (RL) deconvolution 17,18could surpass the Rayleigh criterion in separating double stars in astronomical imaging19. However, such astronomical SR imaging was later shown to be infeasible for solar systems20.Recently, a compressive sensing paradigm also enables SR in proof-of-principle 

experiments2. However, these bandwidth extrapolation methods failed in actual applications because the stable reconstruction depend citicallyonthe accuracy and availbilityofthe assumed a priori knowledge 14–16and logarithmically on the image signal-to-oisatioNR)2.Thusdespitetheteortical feasibility, it is generally agreed that the Rayleigh diffraction limit represents a practical frontier that cannot be overcome by applying bandwidth-extrapolating methods on images obtained from conventional imaging systems14.



a in synthetic, bandwidth-limited, noise-free fluorescence images,but fails in real microscopic images containing noise. With an algorithm that incorporates both sparsity and continuity as the a priori knowledge to constrain the iterative deconvolution followed, we have overcome resolution limits of current SIM9,10,spinning-disc confocal SIM (SD-SIM)24, stimulated emission depletion (STED)5,wide-field, confocal,two-photon25 and expansion microscopes (ExM)26. Therefore, our sparse deconvolution algorithm may help current fluorescence microscopes push their spatiotemporal resolution limits and better resolve intricate, 3D and fast dynamics in live cells.



## Results 

Method execution. Unlike the Wiener deconvolution that operates in the Fourier domain (Supplementary Note 1), iterative RL deconvolution approximates in the space domain and has been proposed to improve resolution under specific conditions1920; however, in practice, it is usually used to reduce out-of-focus blur and noise²728. To understand how RL deconvolution works, we have synthesized ground truth images containing various-shaped structures that were filtered with a band-limited OTF (Supplementary Note 2). Interestingly, sufficient iterations of RL deconvolution largely recovered the high-frequency information in these synthetic images without noise (Supplementary Figs. 1 and 2), thus demonstrating the possible potential of pure computational SR.However, in images corrupted with noise similar to that captured by real-world microscopes, RL deconvolution failed to improve resolution (Supplementary Fig. 2).



In the presence of noise, RL deconvolution quickly converges to a solution dominatedbythe noise aer amall number ofiterations28which constitutes the major problem. Observing the designated structure under any microscope always represents an approximation to the ground truth, in which its accuracy is determined by real biophysical limitations, including the system resolution, the sampling rate and the SNR. For any fluorescence microscope, to ensure sufficient Nyquist sampling criteria for maximal spatial resolution dictated by the optics, the point spread function (PSF) must occupy more than 3×3pixels in space (Supplementary Fig. 3c),which constitutes the basis for the continuity along x and y axes of any fluorescence microscope. Therefore, we used the continuity in xy and also t to suppress noise and subsequent reconstruction artifacts, as we have done before; however, the application of continuity a priori also obscures images and reduces the resolution. We propose introducing sparsity as another prior knowledge to antagonize resolution degradation and extract high-frequency information, because an increase in spatial resolution always leads to a smaller PSF for any given fluorescence microscope. Compared to a conventional microscope, the convolution of the object with the smaller PSF in SR imaging always confers a relative increase in sparsity (Supplementary Fig. 3a,b). Therefore, we believe that continuity and sparsity are general features of the fluorescence microscope that could be used as prior knowledge to suppress noise and facilitate high-frequency information extraction (detailed in Supplementary Note 3).



Overall, we have proposed the following loss function containing these two priors, in which the Hessian matrix continuity is used to reduce artifacts and increase robustness at the price of reduced resolution, and sparsity is used to balance the extraction of high-frequency information:

$$\underset{\mathbf{x}}{\arg\min}\left\{\frac{\lambda}{2}\left\|\mathbf{f}-\mathbf{A}\mathbf{x}-\mathbf{b}\right\|_2^2+R_{Hessian}\left(\mathbf{x}\right)+\lambda_{L1}\left\|\mathbf{x}\right\|_1\right\}$$

The first term on the left side of the equation is the fidelity term,representing the distance between recovered image x and the input image f. Here b is the background estimated using the method described in Supplementary Note 4.3, and A is the PSF of the optical system. The second and third terms are the continuity prior and sparsity prior, respectively.$\|\|_{1}$ and $\|\|_{2}$ are the $\ell_{1}$ and $\bar{\ell}_{2}$ norms,respectively.  and $\lambda_{\mathrm{L l}}$ denote the weight factors balancing the image's fidelity and sparsity. Instead of $\ell_{0}$ norm (absolute sparsity)used as the start point in compressive sensing theory29, we directly used the $\ell_{1}$ norm (sparsity score in Supplementary Fig. 3a), that is,the sum of the absolute values of each element, which can handle both absolutely and relatively sparse structures and constrain the extraction of high spatial frequency information (examples listed in Supplementary Fig. 4). The details for minimizing such convex problems could be found in Supplementary Notes 3 and 4, and the full pipeline is shown in Extended Data Fig. 1.



Improving resolution and contrast in corrupted synthetic images. First, we tested the functionality of different steps in our deconvolution pipeline on synthetic filament structures.While filaments closer than ~100nm could hardly be resolved by Wiener inverse filtering, reconstruction with sparsity a priori created only a small difference in fluorescence of the middle part between the two filaments, while the final deconvolution resulted in clear separation of two filaments down to ~81nm apart (Supplementary Fig. 28a,b). However, the contrast for two filaments ~65 nm apart was low, which could be further improved after the pixel upsampling (labeled as ×2, Supplementary Note 4.4) procedure (Supplementary Fig. 28c,d). Regarding synthetic filament structures corrupted with different levels of noise, deconvolution without the addition of sparsity a priori was unable to retrieve the high-frequency information reliably, while deconvolution without the addition of continuity a priori led to reconstruction artifacts that manifested particularly in raw images with low SNR (Supplementary Fig. 29). Only the combination of continuity and sparsity enabled robust and high-fidelity extrapolation of the high-frequency information inaccessible to SIM, even under situations with considerable noise (Supplementary Tables 1 and 2).



In addition, on deconvolution of synthesized punctated or ring-shaped structures with diameters of 60-120 nm, previous RL deconvolution was only able to resolve rings with diameters larger than 110nm, while more iterations led to overshrink artifacts.By contrast, sparse deconvolution was able to resolve rings with a diameter down to 60nm and produced smaller puncta closely resembling the ground truth (Supplementary Fig. 30). Unlike content-dependent SR via deep learning algorithms0,31,sparse deconvolution could resolve erratic synthetic structures in the same field of view (FOV; Supplementary Fig. 6).



Finally, the poor SNR condition may limit sparse deconvolution in improving resolution. Under extreme noisy conditions,parallel lines after sparse deconvolution sometimes manifested as twisted and fluctuated fluorescence profiles, indicative of artifacts (Supplementary Fig. 7 and Supplementary Note 5). However,compared to RL deconvolution, sparse deconvolution significantly increased the contrast of high-frequency information within the OTF and enabled lines 100 nm apart to be separated (Supplementary Figs. 7 and 8) or better visualization of weakly labeled microtubules under SD-SIM (Supplementary Fig. 9).



Sparse deconvolution resolving samples with known structures.We benchmarked the performance of sparse deconvolution on imaging structures with known ground truth. By low-pass filtering the image obtained by the 1.4-NA objective with a synthetic PSF from a 0.8-NA objective in the Fourier domain, we created a blurred version of actin filaments (Supplementary Fig. 31a,b).Interestingly, two blurry opposing actin filaments under the low-NA objective became separable after sparse deconvolution,along with an extended Fourier frequency domain (Supplementary Fig. 31c,d). Likewise, two neighboring filaments ~120nm apart (confirmed by two-dimensional-SIM (2D-SIM)) were resolved by sparse deconvolution of wide-field images (Supplementary Fig.1e and Supplementary Video15.In addition, a clathrin-coated pit (CCP) of ~135nm in diameter under total internal reflection fluorescence-SIM (TIRF-SIM) manifested as a blurred punctum in wide-field images that had undergone conventional deconvolution or that had been deconvolved with the Hessian continuity a priori.Only after sparse deconvolution did the ring-shaped structure emerge (Supplementary Fig. 31f).Similarly, sparse deconvolution,but not the RL deconvolution, resolved pairs of horizontal lines 150nm apart (Supplementary Fig. 32) and extended OTF of the wide-field microscope (Supplementary Fig. 33).

Next, we designed and synthesized rod-like origami with two fluorescently labeled sites (Methods and Supplementary Fig.34),eachlabeled withfourtofiveCy5orSIM)or AlexaFluor 647 molecules (for repetitive optical selective exposure (OSE)microscopy32). When these molecules were 60, 80 and 100nm apart, they were barely distinguishable under TIRF-SIM but were well separated after upsampling followed by sparse deconvolution (Sparse-SIM ×2; Fig. 1a,b) or under ROSE microscopy (Fig. 1c,d).Furthermore, with one set of parameters, our Sparse-SIM accurately resolved 60/80/100/120-nm interpair distances of DNA origami fluorophores mixed within the FOV (Fig. le,f). Most importantly,the proportions of 60/80/100/120-nm fluorophore pairs observed by Sparse-SIM were comparable to those detected by ROSE microscopy (Fig. 1g). While Sparse-SIM might underestimate the population of 60-nm DNA origami due to its spatial sample at the edge of Nyquist sampling criteria (32 nm per pixel), this hypothesis did not reconcile with the otherwise slightly 'overestimated' 120-nm population compared to ROSE. By contrast, synthetic fluorophore pairs of similar distances were successfully resolved by sparse deconvolution (Supplementary Fig. 35). We wondered whether insufficient sampling of regions of interest in ROSE and Sparse-SIM images may contribute to such minor discrepancies in populations; thus, we included the full ROSE and Sparse-SIM image dataset (Methods)for others to evaluate. Therefore, Sparse-SIM can process more challenging and realistic images containing different and mixed structures. Similarly, one obscure line in the commercial Argo-SIM slide under 2D-SIM could be resolved as two parallel lines 60 nm apart after sparse deconvolution only (Fig. 2a,b). This resolution enhancement was maintained in processing variable SNR images captured under different conditions but failed at extremely low SNRs (1/16SNR; Extended Data Fig. 2),recapitulating previous experiments with the synthetic image (Supplementary Figs. 7 and 8).

Sparse-SIM also resolved ring-shaped nuclear pores labeled with different nucleoporins (Nup35, Nup93, Nup98 or Nup107),while they were similar in size to 100-nm fluorescent beads in the same FOV under 2D-SIM (Fig. 2c,d, Supplementary Fig. 36 and Supplementary Video 1). After correction for narrower fitted diameters of nuclear pores due to camera pixel sizes and pore diameters comparable to the resolution of Sparse-SIM (Supplementary Fig. 25and Supplementary Note 9.1), Nup35 and Nup107 pores were ~66±3nm and ~97±5nm in diameter, respectively, while Nup98and Nup93 pores were of intermediate sizes (Fig.2e,f).These estimations nicely agreed with previous results obtained with different SR methods in fixed cells33-35.Interestingly, 12-min SR imaging enables visualization of the vigorous reshaping of nuclear pores in live cells, possibly reflecting reoriented individual nuclear pore complexes on the nuclear membrane to or away from the imaging plane (Fig. 2g and Supplementary Fig. 37), which would be difficult for other SR methods.



Finally, we tested the reliability of sparse deconvolution in resolving immunofluorescence-labeled complicated structures after ExM26 (Fig. 3). Compared to those obtained by 2D-SIM, tubulin filaments from the 4.5 times-expanded cell after sparse deconvolution were comparable in resolution but better contrasted (Fig. 3a–c).Similarly, while sparse deconvolution of the same expanded complex ER tubules yielded similar overall shapes as those obtained by SIM reconstruction, it was much less affected by artifacts (Fig. 3d,e).Taken together, these data demonstrate a bona fide increase in spatial resolution by sparse deconvolution.



Sparse-SIM achieves ultrafast 60-nm resolution in live cells.Concentrated actin forms a gel-like, dynamic network under the cell cortex with pore diameters of 50-200nm (ref. 36), which are challenging tasks for any live-cell SR methods for the requirement of the combined spatiotemporal resolution. In a COS-7 cell, two actin filaments ~66 nm apart, indistinguishable with either 2D-SIM or Hessian-SIM,were resolved by Sparse-SIM (Fig. 4a-c and Supplementary Video 2). By contrast, applying previously claimed sparsity-based deconvolution algorithms (Supplementary Note 10) produced thinner actin filaments at the price of many amplified artifacts and removed some filaments (Supplementary Fig.27a-c). In sparse deconvolution, better separation of dense actin meshes resulted from both the enhanced contrast (Fig. 4d) and the increased spatial resolution, as shown by the full width at half maximum (FWHM) analysis of actin filaments and Fourier ring correlation (FRC)mapping analysis38,39(Fig.4e,f).This increase in resolution was stable during time-lapse SR imaging of actin dynamics (Fig. 4g), which led to more frequent observations of small pores within the actin mesh. The mean diameter of pores within the cortical actin mesh was ~160nm according to the Sparse-SIM data (Fig. 4h,i), similar to those measured by the stochastic optical reconstruction microscopy (STORM) method in fixed cells36.



An increase in the spatial resolution also helped resolve the ring-shaped caveolae (fitted diameter, ~60nm)(Fig. 4j-l and Supplementary Video 3), which required nonlinear SIM at the Fig.1| Cross-validation of Sparse-SIM and ROSE using DNA origami samples labeled with paired fluorophores of various distances. a, DNA origami samples labeled with paired Cy5 molecules of different distances in the same FOV(60 nm, 80 nm 100 nm and 120 nm) imaged by TIRF (left), TiRF-SIM (middle) and Sparse-SIM ×2 (right) configurations. b,Enlarged regions enclosed by the yellow (60 nm), blue (80 nm), green (100 nm) and red (120nm)boxesinaunderTIRFTIRF-SIMandSparse-SIMx2configurations.c,Anorigamisampleidenticaltowaslabeled withAlexaFluor647andimaged byE.,Miwomelo)lmg)ndm)inc.Fciitoesof theDAmitrctuiabr2fombndSEitromd).BteoiesihtoGinuctions distances weobandkala.,Avaeiabdlhedbr2e)ndSEit);each measurmnt wasepadtntime.g,Pcntageofdifrel labledDAoriamiamplintheimaeobtaiedbySpar-SIM2and ROSE $(n=10)$ ).Centerline,medians; limits,5% and25%;whiskers,maximum and minimum; rror bars,s.e.m.Experiments were repatedfivetimes indepenli;clm(dm 

expense of limited imaging durations and additional reconstruction artifacts10.The fidelity of the reconstruction was confirmed because we did not observe significant artifacts in the error map obtained with the resolution-scaled error analysis3 (Extended Data Fig. 3).For vesicles such as lysosomes and lipid droplets within the cytosol under wide-field illumination, sparse deconvolution reduced 

<div style="text-align: center;"><img src="imgs/img_in_image_box_11_156_1091_1270.jpg" alt="Image" width="90%" /></div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_6_1308_395_1542.jpg" alt="Image" width="32%" /></div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_415_1308_789_1540.jpg" alt="Image" width="31%" /></div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_809_1289_1160_1541.jpg" alt="Image" width="29%" /></div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_20_79_1151_983.jpg" alt="Image" width="94%" /></div>


<div style="text-align: center;">Fig. 2 I Sparse-SIM resolves known structures of -60 nm in size. a,b, Separation of two fluorescent lines with interline spacing down to 60 nm by Sparse-SiM. Raw images were either reconstructed with the Wiener algorithm(2D-SiM) or the Wiener algorithm followed by Fourier interpolation before reconstruction with RL deconvolution for 20(20 RL ×2)or 50 (50 RL ×2) iterations or the sparse deconvolution pipeline (Sparse ×2)(a).The region enclosed by the yellow box was magnified and shown in b. c, A representative example of dynamic ring-shaped nuclear pores labeled with Nup98-GFP in a live COS-7 cell that were observed with Sparse-SIM for more than 10 min. Images under 2D-SIM and Sparse-SIM x2 configurations are shown on the top and bottom, respectively. d, The snapshot of the nuclear pore structure enclosed by the cyan box in c was compared with a 100-nm fluorescent bead under different reconstruction methods (2D-SIM, 20 RL ×2, 50 RL ×2 and Sparse ×2). e, Because the sizes of nuclear pores were comparable to the resolution of Sparse-SIM and the size of the pixel, we followed the protocol in Supplementary Note 9.1 to derive the actual diameters of the nuclear pore structures labeled by Nup3-GFP(ed),Nup-GFPllow,Nup93-FPgreen)andNup17-GFPa,rpctivly.f,Avaediamtrsofigsormdby Nup35$(66\pm3\mathrm{n m};n=30$ from three cells), Nup98$(75\pm6nm;n=40$ from three cells),Nup93(79±4nm;$n=40$ from three cells)or Nup107(97±5nm;$n=40$ from three cells). Left and right montages show the results after Wiener reconstruction or sparse deconvolution.g, The magenta box in c is enlarged and showatsixtimepoint.Cenline,median;limits%and25%;wiskersmaximumandminimum;rorbars,s..m.Expeiments wrea five times independently with similar results; scale bars, 500 nm (c) and 100 nm (d and g). </div>


the background fluorescence and produced high-quality images (Fig. 4m,n and Supplementary Video 4).



By rolling reconstruction with a temporal resolvability of 564 Hz (ref. ), Sparse-SIM could also distinguish fusion pores labeled by VAMP2-pHluorin, which were smaller than those detectable by conventional TIRF-SIM, in INS-1 cells (such as the pore with a fitted diameter of ~61 nm; Fig. 4o,p and Supplementary Videos 5 and 6).In fact, small pores (mean diameter of ~87nm in size corrected following the calibration protocol of nuclear pores) appeared at the early stage of vesicle fusion and lasted for only ~9.5ms; instead,larger pores (~116 nm in diameter) manifested at the later stage of exocytosis and were sustained for ~47 ms (Fig. 4q). For TIRF-SIM,opening times of the initial pores and stationary pores were indistinguishable (~37ms; Fig. 4q), indicating that the early small pore stage was invisible. Nevertheless, although this exocytosis intermediate was not observed by other SR methods, our data agreed with the much lower probability of observing small fusion pores than the larger pores by rapid-freezing electron microscopy reported 

<div style="text-align: center;"><img src="imgs/img_in_image_box_0_102_1143_1318.jpg" alt="Image" width="95%" /></div>


<div style="text-align: center;">Fig.3|Sparse deconvolution-assisted ExM(Sparse-ExM).a,A COS-7 cell was immunostained with a primary antibody against -tubulin and a second antibody conjugated with Alexa Fluor 488.We showed the 4.5 times-expanded cell (ExM-4.5x) in the background and the Sparse-ExM-4.5x image in the center. b,Magnified views of the regions in a under ExM-4.5x,Sparse-ExM-4.5x and ExM-4.5x under 2D-SIM(2D-SIM ExM-4.5x). c, Intensity profiles and multipleGauiainofteilamntareindictdbytewiterowsin b,respctilyNumbrsrpntteditcsbtwnaks; a.uabitrary units.d, ExM images of Sec61β-GFP in a COS-7cell.We showed the ExM-4.5x image in the background and the Sparse-ExM-4.5ximage in the center.e,Enlarged reionsenclosed bthe whitebox indenunder ExM-4.5x,Spare-ExM-4.5xand2D-IMExM-4.5x.Experiments were repeated fivetimes independently with similar results; scale bars, 1m (a,d),300nm (b) and 500nm (e). </div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_6_88_1139_1181.jpg" alt="Image" width="95%" /></div>


<div style="text-align: center;">Fig. 4 Sparse-SIM achieves -60-nm and millisecond spatiotemporal resolution in live cells. a, A representative COS-7 cell labeled with $\mathsf{L i f e A c t-}\mathsf{E G F P}.$ b,c,Enlaredreionnclosed bthewhiteboxinab)andthecorrepondingprofilealonliesc).achboxicdnotetheintnsityofn.d, Average contrasts of two peaks with different distances.$(n=4)$ 1.e, FRC maps of actin filaments.f, Resolutions measured as the FWHM values and by the FRC $(n=20)$ ).g,Time-dependent minimal FRC resolutions.Black trianglesrepresent the theoretical resolution limitof2D-SIM.h,The magnified view of actinfilametintellowoxfrome)ndthegmntdsionri;Mhod)iCumulatieditrbutionofporesieswtithectines inh.j,ApentativeS7lllabled wihcavolin-GFPk,Fromtoptoboomaremaiied viwofthewhiteboxinecnructdby TIRF-SIM,Sparse-SIM andSparse-SIMx2with upsampling(k), and their fluorescence profiles(I).m,Lysosomes were labeled with LAMP1-EGFP (left,llw,d).ofs $(n=10)$ .,Reprenativemontaeofsiclefuinevnt.,KmogaphsromlineinTI-MopandSpar-IM2boom)imaeareshown in $(n=5)$ .Centerline,reults;ler5maeo0mbd),1m)),0mkdmsp)</div>


more than three decades ago40. Beyond that, Sparse-SIM could be readily ued in a dul-olor imain mode toimprove the resoltion at both wavlengths(Extended Data Fig.4),visualizing intricate dynamics within the mitochondria (Supplementary Video 7)and between ER and mitochondria (Supplementary Video 8.

Increasing the 3D resolution of SD-SIM. Because the continuity and sparsity a prioriare neral ature ofR microscopy e teted our aliib-d -4Bimain laeuo s0 dc or alias effects (Supplementary Note 9.2)44 or imaging small beads without corrections, we showed a lateral resolution of ~90 nm and an axial resolution of ~266nm by Sparse SD-SIM (Extended Data Fig. 5), a nearly twofold increase of spatial resolution in all three axes compared to SD-SIM.



In live COS-7 cells labeled with clathrin-enhanced green fluorescent protein (EGFP), Sparse SD-SIM enabled a previously blurred fluorescent punctum to be resolved as a ring-shaped structure with a fited diameter of ~97nm (Fig.5a,b and Supplementary Video 9), which agrees with the resolution given by the beads analysis and the FRC method (Fig.5c) and could not be achieved by other sparsity-based deconvolution methods (Supplementary Fig.27d,e).The median estimated diameter of all the ring-shaped CCPs was ~158nm (Fig. 5d), the same as previously measured with high-NA TIRF-SIM. Events such as the disappearance of a ring-shaped CCP (Fig. 5e) and the disintegration of another CCP into two smaller rings nearby could be seen (Fig. 5f). Because photon budget allowed by Sparse SD-SIM could be as small as ~0.9W cm-2 (Supplementary Table 3), both actin filaments and CCPs within a large FOV of 44m×44μm could be monitored for more than 15min at a time interval of 5s (Fig. 5g, Extended Data Fig.6 and Supplementary Video 16). Under these conditions,many relative movements between CCPs and filaments could be seen. For example, we observed the de novo appearance and the stable docking of a CCP at the intersection of two actin filaments followed by its disappearance from the focal plane as the neighboring filaments closed up and joined together (Extended Data Fig.6d), which is consistent with the role of actin in the endocytosis of CCPs45. Similarly, dual-color Sparse SD-SIM also revealed dynamic interplays between ER tubules and lysosomes, such as the hitchhiking behavior described previously1 (Extended Data Fig.7 and Supplementary Video 17).



Sparse SD-SIM could easily be adapted to four-color SR imaging,allowing the dynamics of lysosomes, mitochondria, microtubules andnuclei to be simultaneously monitored in livecells (Fig.5h,i and Supplementary Video 10) at FRC resolutions as small as 79-90 nm (Fig.5j). Benefiting from the absence of out-of-focus fluorescence and the improved axial resolution, Sparse SD-SIM allowed similar structures to be seen at similar contrast levels throughout the cells,such as mitochondrial outer membrane structures with FWHMs at ~280nm axially (Fig. 5l) maintained in a live cell that was ~7m thick (Fig. 5k and Supplementary Video 11), which was in sharp contrast to the failure of RL deconvolution (Supplementary Fig. 38).Recovering resolution from insufficient Nyquist sampling.Despite their superior quantum efficiency and electron-multiplying capability, the large pixel size of EMCCD (electron-multiplying charge-coupled device) cameras may limit the system resolution.For example, EMCCD-based SD-SIM images of ER tubules after sparse deconvolution conferred an FRC resolution of ~195nm,mostly determined by the undersampling of the pixel size ~94nm (Fig. 6a,b and Supplementary Video 12). We artificially upsampled the image on a finer grid (labeled as ×2; ~47 nm pixel size) before subsequent sparse deconvolution. Along with an increase in the FRC resolution to ~102nm and the expanded system OTF (Fig.6b,d), previously blurred ring-shaped ER tubules became distinguishable (Fig. 6c, indicated by white arrows).



In HeLa cells, we used Sparse SD-SIM to follow dynamic interactions among lysosomes peroxisomes and microtubules in time (Fig.6e and Supplementary Video 13), which could not be resolved by denoise46 or RL deconvolution (Supplementary Fig. 39). Many peroxisomes encounter lysosomes on microtubules, as demonstrated by a lysosome moving along microtubules and colliding with two peroxisomes stably docked closely to the intersection of two tubulin filaments (Fig.6f) or the comigration of a lysosome and a peroxisome along a microtubule for some time before separation and departure (Fig. 6g). These contacts may mediate lipid and cholesterol transport, as reported previously47.



Finally, we observed nuclei, mitochondria and microtubules in a 3D volume spanning ~6μm in the axial axis of a live COS-7 cell (Fig. 6h and Supplementary Video 14). Again, the axial FWHM of a microtubule filament decreased from ~465 nm in the raw dataset to ~228nm after Sparse ×2 processing (Fig. 6i). By contrast, total variation deconvolution4 (Supplementary Fig. 40) failed to improve the xy-z axes contrast. From the volumetric reconstruction, it was apparent that the continuous, convex nuclear structure bent inward and became concave at regions in some axial planes that were intruded by extensive microtubule filaments and mitochondria (Fig.6j,k). Such reciprocal changes suggest that the tubulin network may affect nucleus assembly and morphology 49

## Discussion 

It has been long believed that microscopic optics determine bandwidth limit. Therefore, it is difficult to imagine how sparse deconvolution extracts high-frequency information beyond the microscope OTE. By synthesizing the ground truth image containing various-shaped structures convolved with band-limited PSF, we have shown that RL deconvolution recovers information beyond the spatial frequency limit under the noise-free condition (Supplementary Fig. 1 and Supplementary Note 2). These data instead demonstrate an alternative possibility, in which the total information caried by the microscopeisinvariant5,and adding a priori knowledge (non-negative) may help reveal more details of the object.In this sense, by introducing the sparsity and continuity a priori knowledge to constrain the iterative deconvolution, we have significantly alleviated the problem of converging to artifacts in the presence of noise27.28(Supplementary Figs. 2 and 7). Moreover, by examining the relationship between pixel size and resolution in the raw data, we show that sparsity indeed confers the intrinsic property of the samples, while the continuity prior knowledge must be used to antagonize the loss of information due to inadequate Nyquist sampling (Supplementary Fig. 24 and Supplementary Notes 8.5.

cell.bo $(n=10)$ 1.d,Histogram of viewofthewhiteboxedregioninh.jAverage minimalresolutions bytheFRCmethod $(n=10)$ ).k, 3D distributions of all mitochondria (labeled with bars, 3m(a andi,00nm(e andf,1m (gandI) and5m (hand k.



As we have elaborated in Supplementary Note 3, the sparsity and continuity priors are general features of high-resolution fluorescence microscopes. Correspondingly, using sparse deconvolution on images obtained with the point-scanning confocal microscope,we observed features of nuclear pores and microtubules comparable to those obtained with STED5 (Extended Data Fig. 8). Moreover,

<div style="text-align: center;"><img src="imgs/img_in_image_box_4_155_1162_1535.jpg" alt="Image" width="97%" /></div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_7_90_1149_907.jpg" alt="Image" width="95%" /></div>


<div style="text-align: center;">Fig.UplingableSeItoometeNuistmlilimittoaciveliolorDRimainlivellaERtuble (Sec61β-EGFP) in a live COS-7 cell seen under different configurations.b,Average minimal resolutions by the FRC method.$(n=10)$ ). c, Magnified views of ERtuem.eemea2i transormofa.AtolldtlFarllow.a views in e. As highlighted by white arrows(bottom), only Sparse SD-SIM x2 can dissect the lysosome's deformation by a neighboring peroxisome.g,Time-lapseimagesofanotherexampleofthecomovemntofbothalysosomeandaperoxisomealongamicrotubule.h,Live-cllthre-color (tubulin-EGFPgreen; Hoechst,cyan; MitoTracker Deep Red,magenta)3Dimaging by Sparse SD-SIM×2.i,The z-axial view from h.j,Three horizontal sections of the cellular nucleus(top) and mitochondria merged with microtubules (bottom).k,Color-coded volumes of nuclei, mitochondria and microtubules.Centerline,medians; limits,75% and 25%; whiskers,maximum and minimum; error bars,s.e.m.Experiments were repeated five times independently with similar results; scale bars,5um (a, d, e and h-k),3m (f (top) and g),1um (c) and 500nm (f (bottom))</div>


compared to the normal STED, Sparse-STED also provided increased resolution and showed images of actin, ER and microtubules in live cells at ~40-nm FRC resolution (Supplementary Fig. 41). Finally, sparse deconvolution also extended the observable spatial frequency spectrum of a miniaturized two-photon microscope (MTPM)25, nearly doubled its resolution quantified by the decorrelation method at different axial positions51 and enabled numerous dendritic Thyl-green fluorescence protein (GFP)-labeled spines to be visualized in the live mouse brain (Extended Data Fig. 9 and Supplementary Video 18).



Unlike content-dependent SR imaging achieved by the deep learning algorithms30,31, our sparse deconvolution is content agnostic, such as revealing both rings and punctuated beads in the same FOV (Supplementary Fig. 36), distinguishing both mixed bisected rings and irregular lines (Supplementary Fig. 6) and appreciating tubulin filaments and ER tubules after ExM (Fig. 3). Even for cells labeled with cytosolic $\mathrm{C}\mathfrak{a}^{2+}$ indicators² that were far from absolute sparsity, sparse deconvolution could increase the resolution of SD-SIM without nonlinearly perturbed amplitudes of different $\mathrm{C}\mathtt{a}^{2+}$ transients (Extended Data Fig. 10).All these data endorse our sparse deconvolution algorithm's general applicability in handling different samples captured with various fluorescence microscopes (Supplementary Table 4 and Supplementary Fig. 3).

As a computational SR method, sparse deconvolution faces challenges and caveats often associated with its forerunners, that is, iterative deconvolution algorithms. For example, in addition to resolution enhancement limited by the image SNR (Supplementary Note 5), whether sparse deconvolution provides high-fidelity SR images also depends on the optimal choice of parameters. Having listed all parameters used in the software (Supplementary Notes 

6 and 7), we concluded that we only needed to adjust the fidelity and sparsity values carefully, while their optimal values folow an approximately linear relationship (Supplementary Fg.).It is also worth noticing that high-SNR images afford large fidelity values, while low-SNR images require small fidelity numbers (Supplementary Note 7).Inappropriate choiceof the fidelity and sparsity values may lead to either no increase in resolution, the emergence of artifacts (Supplementary Fig.12)or the removal of weak lsu g.nd.oe,eave provided step-by-step examples in Supplementary Note 8 to guide others to usethesoftware beter and emphasized that any new sructures identified by sparse deconvolution need to be cross-validated by other fluorescence SR methods or electron microscopy.

By reflecting on the principle underlying good' results conferred by visual inspection, we conclude that sparsity and continuity are again the prior knowledge needed for optimal parameter selection. For example, while increasing the sparsity value, we looked for the emergence of additional high-frequency structural information allowed by the Nyquist sampling criteria of the designated resolution from deconvolved images. Although higher resolution may be achievable in images with superior SNR, we selected 60nm as the practical resolution limit for Sparse-SIM to avoid uncertainties associated with overinterfering. For images with a pixel size of ~32nm, appearances of structures (lines, puncta)with an FWHM less than 2pixels (64nm) were often regarded as 'over filtering'artifacts unless more specific prior knowledge is assumed. Otherwise, we advised to turn down the sparsity value.By contrast, sparse deconvolution-reconstructed structures that were larger than or similar in size to those in the original image were due to theover-smooth effects that required down-adjusting the fidelity value. Therefore, such a procedure can be used in biological samples without knowing the prior knowledge of the structures beforehand.



We have also provided several templates for processing different types of structures (Methods).Beyond that, we will continue to explore and share more ts ofparametrs uitablefor difrent types of microscopes, while designing automatic parameter tuning procedures may be another promising solution in the future. However,following Teng-Leong Chew and colleagues' proposition53, we also remind users to keep both the original and deconvolved images intact in addition to the documentation of all parameters. Therefore,by providing the detailed source code, ready-to-use software and example datasets for others to use and explore, we expect our sparse deconvolution method to be broadly tested to push the spatiotemporal resolution limits of current fluorescence microscopes at no additional hardware cost.



## Online content 

Any methods, additional references, Nature Research reporting summaries, source data, extended data, supplementary information, acknowledgements, peer review information; details of author contributions and competing interests; and statements of data and code availability are available at https://doi.org/10.1038/s41587-021-01092-2.



Received: 27 July 2020; Accepted: 10 September 2021;Published online:15 November 2021

## References 

1.Nixon-AbellJ.etalIncreasedspatiotemporalresolutionrevealshihly dynamic dense tubular matricesin the peripheral ER.Science 354,aaf3928 (2016).
reveal theorganelle interactome. Nature 546,162-167 (2017).40nm in living cell membranes discriminates between raft theories. Proc.Natl Acad. Sci. USA 104, 17370-17375 (2007).


4.Shroff,HGalbraitC.GGalbraitJ.A.Betzg,E.Liell photoactivated localization microscopy of nanoscale adhesion dynamics. Nat.Methods5,417–423 (2008).
5.WestaVtal.o-aerfldoticlaocopdssctsyaptic vesicle movement, Science 320, 246–249 (2008).
6. Zhu,L.,Zhang, W,Elnatan,D.& Huang, B.Faster STORMusing compressed sensing. Nat. Methods 9,721-723 (2012).
7.Shin,Wetal.Visualizationofmembrane porein livecellsreveals a dynamic-pore theory governing fusion and endocytosis. Cell 73,934–945 (2018).
8.Godin,A.G.,Lounis, B.& Cognet, L. Super-resolution microscopy approaches for live cell imaging. Biophys.J.107,1777–1784 (2014).9.Huang, X. et al. Fast, long-term, super-resolution imaging with Hessian structured illumination microscopy. Nat. Biotechnol.36,
451–459 (2018).
10. Li, D. et al. Extended-resolution structured illumination imaging of endocytic and cytoskeletal dynamics. Science 349, aab3500 (2015).11. Guo,Y.et al.Visualizing intracellular organelle and cytoskeletal interactions at nanoscale resolution on millisecond timescales. Cell 175,
1430–1442 (2018).
12. Wolter,H.On Basic Analogies and Principal Diferences Between Optical and Electronic Information, Vol.1 (Elsevier, 1961).
13. Harris, J. L. Diffraction and resolving power. J. Opt. Soc. Am. 54,
931–936 (1964).
14. Goodman, J. W. Introduction to Fourier Optics (Roberts and Company Publishers, 2005).
15.Lindberg, J.Mathematical conceptsof optical superresolution.J.Opt.4083001 (2012).
16. Bertero, M. & De Mol, C. Super-Resolution by Data Inversion, Vol. 36(Elsevier, 1996).
17. Richardson, W. H. Bayesian-based iterative method of image restoration.J.Opt. Soc.Am.62,55–59 (1972).
18.Lucy,L.B.An iterative technique for the rectification ofobserved distributions.Astron.J.79,745(1974).
19. Lucy, L. B.Resolution limits for deconvolved images. Astron. J.104,
1260-1265(1992)
20. Puschmann, K. G. & Kneer, E. On super-resolution in astronomical imaging.
Astron.Astrophys.436,373-378(2005)
21. Gazit, S.,Szameit,A.,Eldar, Y. C.& Segev, M. Super-resolution and reconstruction of sparse sub-wavelength images. Opt. Express 17,23920-23946 (2009).
22. Demanet, L. & Nguyen, N. The recoverability limit for superresolution via sparsity.Preprint athttps://arxiv.org/abs/1502.01385 (2015).23. Fannjiang, A. C. Compressive imaging of subwavelength structures. SIAM J.
Imaging Sci. 2,1277–1291 (2009).
24.Schulz, O.et al.Resolution doubling in fluorescence microscopy with confocal spinning-disk image scanning microscopy. Proc. Natl Acad. Sci. USA 110, 21000-21005 (2013).
25. Zong, W. et al. Fast high-resolution miniature two-photon microscopy for brain imaging in freely behaving mice.Nat.Methods 14,713-719 (2017).26. Sun, D.-E. et al. Click-ExM enables expansion microscopy for all biomolecules.Nat.Methods18,107-113 (2021).
27.Dey, N.et al. Richardson-Lucy algorithm with total variation regularization for 3D confocal microscope deconvolution. Microsc. Res. Tech.69,
260-266 (2006).
28. Laasmaa, M., Vendelin, M. & Peterson, P. Application of regularized Richardson-Lucy algorithm for deconvolution of confocal microscopy images.J.Microsc.243,124-140(2011)
29.Candes, E.J. & Tao, T.Near-optimal signal recovery from random projections: universal encoding strategies? IEEE Trans. Inf. Theory 52,
5406-5425(2006)
30.Hoffman,D.P.,Slavitt,I.& Fitzpatrick, C.A.The promise and peril of deep learning in microscopy. Nat. Methods 18, 131–132 (2021).31.Belthangady,C.&Royer,L.A.Applications,promises,and pitfalls of deep learning for fluorescence image reconstruction.Nat. Methods 16,
1215–1225 (2019).
32. Gu, L.et al. Molecular resolution imaging by repetitive optical selective exposure. Nat. Methods 16, 1114–1118 (2019).
33.Szymborska,A.et al.Nuclear pore scaffold structure analyzed by super-resolution microscopy and particle averaging. Science 341,
655–658(2013).
34. Ma, J., Kelich, J. M., Junod, S. L. & Yang, W. Super-resolution mapping of scaffold nucleoporins in the nuclear pore complex. J. Cell Sci. 130,
1299–1306 (2017).
35. Gottfert,E.et al. Strong signal increase in STED fluorescence microscopy by imaging regions of subdiffraction extent. Proc. Natl Acad. Sci. USA 114,
2125-2130(2017)
36.Xia, S.et al. Nanoscale architecture of the cortical actin cytoskeleton in embryonic stem cells. Cell Rep. 28,1251-1267 (2019).

37.SzameitA.etal.Sparsity-based single-shot subwavelength coherent diffractive imaging. Nat. Mater. 11, 455–459 (2012).
38.Nieuwenhuien,R.Petal.Measuringimagereolutioninopticalnanoscop.Nat.Methods 10,557–562 (2013).
39.Culley,S.etal.Quantitative mappingand minimizationof super-resolution optical imaging artifacts.Nat. Methods 15, 263-266 (2018).40. Ornberg, R. L. & Reese, T. S. Beginning of exocytosis captured by rapid-freezing of Limulus amebocytes.J. Cell Biol.90, 40–54 (191).41.York,A.G.etal.Intantuper-reolutioimagingin livecllsandmbryos via analog image processing. Nat. Methods 10, 1122-1126 (2013.42.York,A.G.t al.Rolution doublg in liveltillulraim via multifocal structured illumination microscopy. Nat. Methods 9,749–754 (2012).
43.Muller,C.B.&Enderlein,J.Image scanningmicroscopy.Phy.Rev.Lett.104198101 (2010).
44. Theer, P, Mongis,C.& Knop, M.PSFj: know your fluorescence microsope.
Nat. Methods 11, 981-982 (2014).
45.Saffarian,S.,Cocucci,E.&KirchhausenT.Distinct dynamics of endocytic clathrin-coated pits and coated plaques. PLoS Biol. 7,
e1000191 (2009).
46.Luisier, E,Vonesch,C., Blu, T.& Unser, M.Fast interscale wavelet denoiing of Poisson-corrupted images. Signal Process. 90, 415-427 (2010).

47. Chu, B. B. et al. Cholesterol transport through lysosome-peroxisome membrane contacts. Cell 161, 291–306 (2015).
48.Wang, Y.,Yang, J.,Yin, W. & Zhang,Y. A new alternating minimization algorithm for total variation image reconstruction. SIAM J. Imaging Sci.1,248-272 (2008).
49.Xue, J. Z.& Funabiki, H. Nuclear assembly shaped by microtubule dynamics.
Nucleus 5, 40–46 (2014).
50. Cox, C. I. & Sheppard, C. Information capacity and resolution in an optical system. J. Opt. Soc. Am.A 3,1152-1158 (1986).
51.Descloux, A., GruBmayer, K.S.& Radenovic, A.Parameter-free image resolution estimation based on decorrelation analysis. Nat. Methods 16,918–924 (2019).
52. Zhang, Y.et al.Mitochondria determine the sequential propagation of the calcium macrodomains revealed by the super-resolution calcium lantern imaging. Sci. China Life Sci.63, 1543-1551 (2020).
53.Aaron, J. & Chew, T.-L.A guide to accurate reporting in digital image processing—can anyone reproduce your quantitative analysis? J. Cell Sci. 134,jcs254151 (2021).
PublishersnoteSpringerNatureremainsnutral withregardtojurisdictionallaimsin published maps and institutional affiliations.
©The Author(s),under exclusive licence to Springer Nature America,Inc.2021

## Methods 

The interference-based SIM setup. The SIM system is based on a commercial inverted fluorescence microscope (IX83, Olympus) equipped with two TIRF objectives(×100/1.7HI oil, APON,Olympus;×100/1.49oil, UAPON, Olympus),a wide-field objective (x100/1.45 oil, APON, Olympus) and a multiband dichroic mirror (ZT405/488/561/640-phase R, Chroma), as described previously.In short,laser light with wavelengths of 488 nm (Sapphire 488LP-200) and 561 nm (Sapphire 561LP-200, Coherent) and acoustic optical tunable filters (AA Opto-Electronic)were used to combine, switch and adjust the ilumination power of the lasers.A collimating lens (focal length,10mm; Lightpath) was used to couple the lasers to a polarization-maintaining single-mode fiber (QPMJ-3AF3S, Oz Optics. The output lasers were then collimated by an objective lens CFIPlan Apochromat Lambda x2/0.10-NA, Nikon) and diffracted by pure-phase grating that consisted of a polarizing beam splitera half-wave plate and the ferroelectric liquid crystal spatial light modulator (3DM-SXGA, ForthDD).The diffraction beams were then focused by another achromatic lens (AC58-250, Thorlabs) onto the intermediate pupil plane.Acarefully designed stop mask was placedtoblock the ero-rder beam andother stray light and to permit passageof±lorderedbeam pairs onlyT maximally modulatethe illumination paternwhileeliminatingthe switchingtime between diferentexcitation polarizations,we placed ahome-made polarization rotator after the stop mask.Next, the light passed through another lens (AC254125,Thorlabs) and a tube lens (ITL200,Thorlabs) to focus on the back focal plane oftheobjctivelnhichitredwiththeimaelanear singthouh theobjectivelen.Emitdfluorescncecollctedbytheameobjectivesed tholl animage spltter (W-VIEW GEMINI, Hamamatsu) before the sCMOS camera (Flash .amamtu)tolitthedflucochannels.

The SD-SIM setup.TheSD-SIM is a commercial system based on an invered fi (×100/1.3oil,Olympus)and canningconfocalstemCSU-X1,Yokogawa).Four laser beams of 405 nm, 488nm,561nm and 647nm were combined with the SD-SIM. The Live-SR module (GATACA systems) was equipped with the SD-SIM. The images were captured either by an sCMOS camera (C1440-20UP,Hamamatsu) or an EMCCD camera (iXon3 897, Andor), as mentioned in Figs.5 and 6.



The ROSE setup. ROSE microscopy and the reconstruction step was previously describedinref.For DNAorigami,anexposureof50msan EMgainof50 and anillumination power intensityof4kWcm−wereused.Atotalof20.00frames were acquired for reconstruction. During imaging, a 405-nm laser was used to control molecule density, with an intensity of 0-10W cm−2.

The STED setup. Image acquisition of STED was obtained using a gated STED microscope (Leica TCS SP8 STED 3X, Leica Microsystems) equipped with a wide-field objective (×100/1.40 oil, HCX PL APO, Leica). The excitation and depletion wavelengths were 488 nm and 592 nm for Sec61β-GFP and LifeAct-GFP 594nm and 775nm for Alexa Fluor 594,635 nm and 775 nm for Alexa Fluor 647and 651 nm and 775 nm for SiR-tubulin. The detection wavelength range was set to 495–571nm for GFP, 605-660nm for Alexa Fluor 594,657-750nm for SiR and 649-701 nm for Alexa Fluor 647.For comparison, confocal images were acquired in the same field before STED imaging. All images were obtained using LAS AF software (Leica).



The MTPM setup. Animals were housed on a 12-h light/12-h dark cycle at 22C with free access to food and water. A male 3-to 5-month-old Thy1-GFP transgenic (C57BL/6J) mouse was used. The mouse was awake, and the head was fixed under the MTPM25 (FHIRM TPM-V1.5, Transcend Vivoscope Biotech) in vivo by using a micro-objective with an NA of 0.7.The FOV of the microscope was 190×190μm2,the frame rate was 13 Hz (512×512 pixels) and the working distance was 390 μm.The 3D imaging was from 50 μm to 160 μm below the cortex with 1-μm slices. The raw stack captured by MTPM was registered by the rigid body transformation before further processing and visualization.



Cell maintenance and preparation. INS-1 cells (Sigma, SCC207) were cultured in RPMI 1640 medium (Gibco, 11835-030) supplemented with 10% fetal bovine serum (FBS; Gibco),1% 100mM sodium pyruvate solution and 0.1%55mM 2-mercaptoethanol (Gibco, 21985023) in an incubator at 37C with 5% CO2until ~75% confluency was reached.COS-7 cells (ATCC, CRL-1651) and HeLa cells (ATCC, CCL-2) were cultured in high-glucose DMEM (Gibco, 21063029)supplemented with 10% FBS (Gibco) and 1% 100mM sodium pyruvate solution (Sigma-Aldrich,S8636) in an incubator at 37C with 5% CO, until ~75%confluency was reached. For the 2D-SIM imaging experiments, cells were seeded onto coverslips (H-LAF 10L glass; reflection index,1.788; diameter, 26 mm;thickness, 0.15 mm, customized).For the SD-SIM imaging experiments, 25-mm coverslips (Fisherbrand, 12-545-102) were coated with 0.01% poly-L-lysine solution (Sigma) for~24h before seeding transfected cells. For bead imaging, the 100-nm-diameter fluorescent beads (Thermo Fisher Scientific, T7279) were diluted to 1:100 in PBS.



Live-cell samples. For the 2D-SIM experiments, to label late endosomes or lysosomes, COS-7 cells were incubated with 1× LysoView 488 (Biotium,70067-T)in complete cell culture medium at 37C for 15-30 min and protected from light,without being washed, and imaged. To label late endosomes and lysosomes in the SD-SIM experiments, we incubated COS-7 cells in 50 nM LysoTracker Deep Red (Thermo Fisher Scientific, L12492) for 45 min and washed them three times in PBS before imaging. To label lipid droplets,COS-7 cells were incubated with 1×LipidSpot 488 (Biotium,70065-T) in complete cell culture medium at 37C for 30 min and protected from light before being washed and imaged. To label mitochondria, COS-7 cells were incubated with 250 nM MitoTracker Green FM(Thermo Fisher Scientific, M7514) and 250nM MitoTracker Deep Red FM (Thermo Fisher Scientific,M22426) in HBSS containing Ca2+and Mg2+orno phenolred medium (Thermo Fisher Scientific,14025076) at 37C for15min beforeing ed thetimebforeimig.To rorm uclar taining COS-7cellswereincubated ith10gmlHoechstThermosher Scientific,

Toa caveolin-EGFP/LifeAct-EGFP/LAMP1-EGFP/LAMP1-mCherry/Tom20mScarlet/Tom20-mCherry/Sec61β-mCherry/Sec61β-EGFP/clathrin-EGFP/clathrin-DsRed.Foralciumimainexpriments,O-7llswretransfected with GCaMP6s.To label nuclear pores, COs-7 cells were transfected with GFP–Nup35/GFP-Nup93/GFP-Nup98/GFP-Nup107. HeLa cells were transfected with tubulin-EGFP/Pex1la-BFP/LAMP1-mCherry. INS-1 cells were transfected with Vamp2-pHluorin. The transfections were executed using Lipofectamine 2000(Thermo Fisher Scientific,11668019) according to the manufacturer's instructions.After transfection, cells were plated on precoated coverslips. Live cells were imaged in complete cell culture medium containing no phenol red in a 37C live-cell imaging system.For thecalcium lantern imaging in SD-SIM,calcium signal was stimulated with amicropipettecontaining10μmol liter5-ATP-Na2solutions (Sigma-AldrichA12).ForexperimentsonductedwitINS-1lls,thells were stimulated with a solution containing 70 mM KCl and 20 mM glucose, and vesicle fusion events were observed under a TIRF-SIM microscope.

Samples for SIM imaging. DNA origami materials. M13mp18 phage DNA was purchased from New England BioLabs and used withoutany further purification.All staple strands,including Cy5/Alexa Fluor 647-modified and biotin-modified staple strands, were purchased from Sangong Biotech. The Cy5/Alexa Fluor 647-labeled and biotin-modified staple strands were purified by denaturing polyacrylamidegllectrophoresis (AGE) withtherestofthestaplestrandsused as received without further purification.TheDNA origami staple strands were premixed and stored in 1.5-ml Eppendorf tubes at -20C.

DNA origami design and assembly. The 14-helix bundle DNA origami nanostructure(14HB) was designed with a lengthof178nm using theopensource software caDNAno5.Structural integrity and rigidity were examined using the online modeling server Cando5657.We mixed scaffold strands, staple strands and Cy5-or Alexa Fluor 647-modified staple strands at a molar ratio of 1:10:10 in 1x TAE buffer (with 18 mM Mg2+).The mixed solution was annealed in a Bio-Rad PCR thermocycler using the following program: from 95C to 65C (5min perC),from 65°C to 45°℃(90min perC) andfrom 45℃to 25℃C (10 min per C). After the annealing process, the DNA origami nanostructures were purified using 2% agarose gel electrophoresis. Finally, the DNA origami nanostructures were extracted from the gel and stocked in 1x TAE/Mg²+ buffer for further use.



Preparing DNA origami samples for SIM/ROSE imaging. To immobilize DNA origami on the surface, the DNA origami was modified with 18 biotinylated staple strands that can bind to a bovine serum albumin (BSA)-biotin-streptavidin-coated SIM cover glass surface. For ROSE imaging, polystyrene microspheres (Wuhan Huake Weike Technology, PS-M-10075) were added on the cover glass for system calibration. Overall the cover glass was processed as described in ROSE. DNA origami structures were mixed with 60/80/100/120-nm structures at a molar ratio of 1:1:1:1 in 100μl of PBS with 10mM MgCl.Then,100 l of mixture was pipetted onto the cover glass and incubated for 5 min. After three PBS washes,the sample was ready for imaging. STORM imaging buffer used for ROSE consisted of 1x PBS buffer, 10% glucose, oxygen removed, GLOX (glucose oxidase (0.6mgml-1) and catalase(0.06mgml-1) dissolvedin Tris-HClbuffer)and143mM 2-mercaptoethanol.



Argo-SIM slide. To validate the increase in resolution, we used a commercial fluorescent sample (the Argo-SIM slide, Argolight) with ground truth patterns consisting of fluorescing double line pairs (spacing from 0nm to 390nm;λ=300550nm) (http://argolight.com/products/argo-sim).



Sample preparation for ExM.α-Tubulin immunostaining. COS-7 cells were seeded in a Lab-Tek II chamber slide (Nunc, 154534).Cells were first extracted incytoskeletonextractionbufer(.2%(vol/vol)TritonX-100,0.1MPIPES 1 mM EGTA and 1mM MgCl,pH 7.0) for 1 min at room temperature. Next,the extracted cells were fixed with 3% (wt/vol) formaldehyde and 0.1% (vol/vol)

glutaraldehydefor15minreducedith0.1%(wt/vol)NaBHinPBSfor7minand 0.1%vol/vol)TtonX-100or15minandblockedwith5%(w/vol)SAin0.1%(vol/vole2oriFtiodaiglsicubaeth monoclonal rabbitanti--tubulin(1:250dilution;EP1332Y,Abcam,ab52866) in antibodilutonbuff.%/v)i%l/ol)T)vt at 4C, washed three times with 0.1% (vol/vol) Tween 20,incubated with Alexa Fluorjuaib:l Thermo,A07) in antibodydilution bufer for2h atroomtemperature and washed three times with 0.1% (vol/vol) Tween 20.



Sec61β-GFP transfection.COS-7 cells were seeded in aLab-TekII chamber slide (Nunc, 154534) and cultured to reach around 50% confluence.For transient transfection of Sec61β-GFP in a single well50ngof plasmid and 1 l of X-tremeGENE HP (Roche) were diluted in 20 l of Opti-MEM sequentially. The mixture was vortexed, incubated for 15 min at room temperature andappliedtoclls.Twentyfourhours aftertransfection,thecellswere washed three times with PBS and fixed as described in the α-tubulin immunostaining experiment.



Sample expansion. The sample expansion was performed as previously described2658.Labeledcellswereincubatedwith0.1mgmlof Acryloyl-X (Thermo, A20770) diluted in PBS overnight at room temperature and washed three times withS.To prparetheglationolutionreshly prpared%w/wt) N,N,NNetramethylethylenediamine(TEMED;Sigma,T7024)and10%(wt/wt) ammonium persulfate (APS; Sigma, A3678) were added to the monomer solution(1×PBS,2MNaCl,2.5%(wt/vol) acrylamide(Sigma,A9099),0.15%(wt/vol) N,N'-methylenebisacrylamide (Sigma, M7279) and 8.625% (w/vol)sodiumacrlaegma,2))tofialocioof2%w/)ach.Next,thecellswereembedded withthegelationsolutionfirstfor5min at 4℃and then for lh at 37C in a humidified incubator. The gels were immersed into the digestion buffer (50mM Tris,1mM EDTA, 0.1% (vol/vol) Triton X-00 and 0.8Mguanidine HCl,pH 8.0)containing 8Uml proteinase K(New England BioLabs, P8107S) at 37C for 4h and then placed into double-distilled water to expand. Water was changed four to five times until the expansion process reached a plateau. By determining the gel sizes of before and after the expansion, we quantified the expansion factor to be 4.5 times.The gels were immobilized on poly-D-lysine-coated glass no. 1.5 cover glass for further imaging.

Samples for STED imaging. To label the ER tubules/actin/microtubule in live cells,COS-7 cells were either transfected withSec61β-EGFP/LifeAct-EGFP or incubated withSiRtubulin(cytoskeleton,CY-C02)for~20minwithout washing before imaging. For immunofluorescence experiments, HeLa cells were quickly rinsed with PBS and immediately fixed with prewarmed 4% paraformaldehyde (Santa Cruz Biotechnology, sc-281692).After rinsing three times with PBS, cells were permeabilized with 0.1% Triton X-100 (Sigma-Aldrich, X-100) in PBS for 15min. Cells were blocked in 5% BSA/PBS for 1h at room temperature.Cells were incubated with primary antibodies (monoclonal mouse anti-Nup107, Mab414,1:1,000 dilution, Abcam,ab24609;mouse anti-Tom20,1:1,000 dilution,29/Tom20,BD Biosciences,612278;monoclonal rat anti-tubulin, YL1/2, 1:1,000 dilution,Abcam,ab6160) diluted in 2.5% BSA/PBS blocking solution in a 4C cold room overnight followed by a final wash in PBS.Secondary antibodies (goat anti-mouse conjugated to Alexa Fluor 594,Abcam,ab150120; goat anti-rat conjugated to Alexa Fluor 647, Abcam, ab150167) were used at concentrations of 1:500 and incubated in 2.5% BSA/PBS blocking solution at room temperature followed by washing.

Usage of sparse deconvolution software. In the Supplementary Software user interface, we included 13 parameters to adapt to different hardware environments,experimental conditions and fluorescence microscopes (Supplementary Fig. 10).To simplify the usage of software, we have classified them into three categories:fixed parametrs,image property parameters andcontnt-aare prameters.We have explained these parameters in detail in Supplementary Note 6.In short, the ten parameters in the first two categories are primarily determined by the optical system and image property and hardly need tuning. Only the three content-aware parameters need to be adjusted back and forth carefully by visual examination of the reconstructionresults.In Supplementary Note 7,wediscussedideal values ofsparsity andfidlityunderdferentexperimentalconditions.Whilthe optimal values of fidelity and sparsity follow an approximately linear relationship,high-SNR images afford large fidelity values, while low-SNR images require small fidelity numbers. In Supplementary Note 8, we have introduced a four-step procedure for parameter finetuning,five step-by-step examples of adjusting the sparsity and fidelity toobtain optimal reconstructions and more explanations on the background estimation in the end 



FRC resolution map and other metrics. FRC resolution was implemented to describe theeffectiveresolutionof the SRmicroscope.To visualize theFRC resolutomely,wapitelc-eCg described inref.toevaluate our (Sparse) SIM and (Sparse) SD-SIMimages. More speciflotk 

valueiscalculatedindividuallyusingthemethodreportedinref..IftheFRC estimaionsinblockareufitlyorladtisgionwllboloroded in the FRC resolution map. Otherwise,the region will be color coded according toits neighbor interpolation.Note that before calculating the FRC resolution map of SD-SIMrawimagesinFigs.5ahanda,adenoisemethod4wasapplied in advance to images to avoid the ultralow SNR of SD-SIM raw images perturbing the FRC calculation. We also used the structural similarity values and peak SNR to evaluate the quality of reconstructions in Supplementary Fig.2.

Synthetic filament structures under SIM imaging. We created synthetic filament structures using the 'Random Walk' process and adopted the maximal curvatures in the program, generating the filament structures (Supplementary Fig. 29a).To simulate time-lapse sequences of filament structures, we used a subpixel shift operation to generate a random shift in these filaments based on the'Markov chain'in the t axis,resulting in an image stack of 128×128×5 pixels. To mimic SIM acquisition, these ground truth objects were iluminated by pattern excitation and convolved with a microscope PSF (1.4NA, 488 nm excitation, 32.5 nm pixel)to generatewide-fieldrawimages.Inadditiontothefilaments,wealsoincld abackground signal that combined the effects of cellular autofluorescence and fluorescence emitted from the out-of-focus plane (simulated by the convolution of synthetic filaments with out-of-focus PSF 1m away from the focal plane).Moreover, we incorporatedGaussian'noise with diferent variance extents %11%,25%,50%,80%)to the peak fluorescence intensity of the filaments.The raw images were acquired by a camera with a pixel size of 65 nm and pixel amplitudes of 16 bits (Supplementary Fig. 29b).



Corrections of bead FWHMs and pore diameters. To extract FWHMs of fluorescent beads and linear structures and the double-Gaussian peak in ring structures, we used the multiple-peak fit of the Gaussian function in OriginPro.When the sizes of the the system PSF and the size of the camera pixels were comparable to the size of the structure been imaged,fitted diameters of punctated andring-shaped structures differently deviated from their real values(Fig.2e, Extended Data Fig. 5c, Supplementary Figs. 25 and 26 and Supplementary Note 9). For narrowed fitted diameters of nuclear pores and fusion pores under Sparse-IMig.and),worctdtealuesollowingtheprotocolin Supplementary Note 9.1. For apparent enlarged sizes of fluorescent beads under the microscope (Supplementary Fig. 26 and Supplementary Note 9.2), we included abead sizecorrectionfactor for beads with a diameterof 100nm to estimatethe real resolution of Sparse SD-SIM (Extended Data Fig. 5c).



Mesh pore diameters of actin networks.We analyzed the mesh pore diameters (Fig.4h)ofactinnetworksbasedonthepipelineinref.3.Consideringthe low-SNR condition and high background in 2D-SIM and SD-SIM images, we replaced the pretransform 36,6]with the prefilter.Specifically,weused a Gaussian filter and an unsharp mask filterto denoise the raw image and remove its background sequentially. To do so, we extracted the pores by Meyer watershed segmentationThe pore sizescanthenbecalculatedby thenumberofenclosed pixels frominvertedbinaryimagesmultipliedbythephysical pixel sze.Itisworh noting thatSparse-SMand SparseSD-SMimagescanbesegmented directly using hard thresholds due to their low backgrounds.



CCP diameters.Following the pipeline in ref.,two main procedures are involved beforecalculatingtheCCPdiametersinFig.a.Firstheimageing.ais segmented withthe locally adaptivethresholdtoleave thering structuresin the image. Second, the resulting binary images are processed by the Meyer watershed after distance transform to separate touching CCPs.Subsequently, the CCP diameters can be calculated in the same manner as the mesh pore diameters.Finally, a correction of the CCP diameters is also included the same as described in the protocol in Supplementary Note 9.1.



Precompenating forthkewedintenityditibution.Fluorecenceimages are prone to shadingand vignetingefects,whichmay perturb laer processing and analysis. Thus, we chose BaSiCas a precorrection option before sparse deconvolution.BaSiC is based on a linear imaging model that relates the measured image,(lcioniucrrudcuonc Such a linear model can be expressed as $\bar{I}^{\mathrm{mess}}(x)=\bar{I}^{\mathrm{ruc}}(x)\times\bar{S}(x)+\bar{D}(x)$ ,where S(x)representsthecangeinctivellumtioncrsanimagenowas flt field), and the additive term D(x) (known as the dark field) is dominated by the cameraoffetanditsthermalnoisethatarepresentevenintheabsenceofinident light.BaSiCestimates S(x) and D(x) by low rank and sparse decomposition to correct thehadinginspaceandbackgroundvaiaionsintime.Weued BaSiCo correcttheunevenilluminationto avoid removingweak signals attheedgeofthe FOVinthe following dconvolution procss (Supplementary Fig.21be).However weshalleusiigi degraded images.



Image rendering and processing.Thecolor map SQUIRREL-FRC associated with ImageJ was used to present the FRC map in Fig.4e.Thecolor map MorgenstemningwasappliedtoshowlysosomesinFig.5handtheFourier 

talinx..pj Data ree bDrillaidI.ll fi v l available at https://github.com/WeisongZhao/img2vid.



The.l (1)xltbitlra hotcamerpil.Themagtueoftheixlsrapproximlytom hierrlttorceolae pill wch anadapiveeianftrtormoveeiroper pil.oespcifically insteadofteoralianfwhichrelacac pilwtemian of the neighboring pixels in the window,we set a threshold for our developed adaptivemedianfilterIfthe pixel intensity is larger than thresholdxmedianin the window,tepilisrelacedbthemeinerwitheinwmoes nextl.uto,ecaolpilsotlui the images.



GPU acceleration. We implemented sparse deconvolution in MATLAB using a centalriut;Il,.Hz10ea 128GB memory),the NVIDICUDAfast Fouier transform library (cuFFT)andaapcsnuitGU;N,4Aen4B mmo.oal matrixcoil GPUmmoriufiintfortheiputdclriocomsrevit asthe sizeofthedataincrease.Inmostcircumstances,a5-foldimprovementwas achievd oo.ae imaeao2inreose farless4edortteftor/GU datacomputing times in Figs.2-5canbe foundin Supplementary Table5.

Reporting Summary.Further information on research design is available in the Nature Research Reporting Summary linked to this article.

## Data availability 

R templates for processing different types of structures along with example datasets canbe found at https://github.com/WeisongZhao/Sparse-SIM/releases/tag/v1.0.3orhttps://doiorg/10.21/zenodo.579743.Allotherdatathatsupportthefndings ofthis study are availablefrom the corresponding author on request.

## Code availability 

Our light-weight MATLAB framework for video production is available at https://github.com/WeisongZhao/img2vid.Ouradaptive filterhasbeenwritten asan Image plug-inandcanbefound athttps://github.com/WeisongZhao/AdaptiveMedian.imagej. The version of sparse deconvolution software used in this manuscript (accompanied with a user manual) is available as Supplementary Software. The updating version of readily usable executable binary files for Windows(asexe)andMac(asapp)operatingsystemscanbefoundath://github.com/WeisongZhao/Sparse-SIM/releases/tag/v1.0.3and thecorresponding source code can be found at https://github.com/WeisongZhao/Sparse-SIM.

## References 

54.Thévenaz, P, Ruttimann, U.E.& Unser,M.A pyramid approach to subpixel registrationbasedonintensity.IEEE Trans.ImageProcess.7,27-4(1998.55.Douglas,S.M.et al. Rapid prototypingof 3D DNA-origami shapes with caDNAno.NucleicAcids Res.37,5001-5006 (2009).
56.Kim,D.-N.,Kilchherr,F,Dietz,H.&Bathe,M.Quantitativepredictionof 3Dsolution shapeandflexibilityof nucleicacid nanostructures.NuleicAids Res.40,2862-2868 (2012)
57.Castro,C.E.et al.A primer to scaffolded DNAorigami. Nat.Methods 8,
221–229 (2011).
58.Tillberg,P.etal.Protein-retention expansionmicroscopyofcells andtissues labeled using standard fluorescent proteins and antibodies. Nat. Biotechnol.34, 987–992 (2016).


59.Wang, Z.,Bovik,A.C.,Sheikh,H.R.& Simoncelli,E.P.Imagequality assessment:from error visibilityto structural similarity.IEEE Trans.Image Process. 13, 600-612 (2004).
60.Weigert,M.etal.Content-awareimage restoration:pushingthe limitsof fluorescence microscopy. Nat. Methods 15, 1090-1097 (2018).61. Zhang, Z.,Nishimura,Y. & Kanchanawong, P. Extracting microtubule networks from superresolution single-molecule localization microscopy data.Mol.Biol.Cell 28,333–345 (2017).
62.De VriesF.P.Automatic,adaptive,brightness independent contrast enhancement. Signal Process. 21,169-182 (190).
63.Meyer, F.& Beucher,S.Morphological segmentation. J. Vis.Commun.Image Represent. 1, 21–46 (1990).
64.Yanowitz, S. D.& Bruckstein,A.M.A new method for image segmentation.Comput. Gr. Image Process. 46, 82-95 (1989).
65. Peng, T.et al.A BaSiC tool for background and shading correction of optical microscopy images. Nat. Commun. 8,14836 (2017).
66. Geissbuehler, M. & Lasser, T. How to display data by color schemes compatible with red-green color perception deficiencies. Opt. Express 21,9862–9874 (2013).
67.Royer,L.A.et al.ClearVolume: open-source live 3D visualization for light-sheet microscopy. Nat. Methods 12, 480–481 (2015).68.Schmid,B.et al. 3Dscript: animating 3D/4D microscopy data using a natural-language-based syntax. Nat. Methods 16, 278–280 (2019).

## Acknowledgements 

We thank B.Hille and C.Xu for their reading and critical comments on the manuscript.We thank M.Knop and P. Theer for their feedback and valuable discussions of the bead correction factor and C.Zhang and J.Ma for the sharing of nuclear pore vectors. We thanktheNational CenterforProteinSciencesatPekingUniversityin Beijing,China,for assistance with STED imaging experiments.L.C.acknowledges support by grants from the National Natural Science Foundation of China(nos 92054301,81925022,31821091and91750203),the National Science and Technology Major Project Program (no.2016YFA0500400)andtheBeijingNaturalScienceFoundation(no.20J00059).H.L.acknowleesuportbgrantsfromtheNationalNatualcienceFoundationofChina (no.61805057),theYoungEliteScientistsSponorship Program(no.2018QNRC001)andtheNatual cienceoundatioof Hiloiangrovnce22F).L.C.acknowledges support by the High-Performance Computing Platform of Peking University.H.L.and J.L.acknowledge support by the State KeyLaboratoryof Robotics andSystems.S.Zhao acknowledges support by the Boya Postdoctoral Fellowship of Peking University.H.M. acknowledges support by grants from the National Natural ScienceFoundationofChinano.325).YL.acknowledgessuportbygrantsfrom the National Natural Science Foundation of China (no. 9184112).

## Author contributions 

L.C. and H.L. supervised the project. W.Z.,H.L., L.C. and X.H.initiated and conceived the research. W.Z.developed the algorithm and implemented the corresponding software with the contribution and under the supervision of H.L. L.L.,X.H.and S.X.performed the SIM experiments. S.Zhao and Y.Z. performed the SD-SIM experiments. S.Z.and C.S. performed the STED experiments. R.W. performed the MTPM experiments. L.G.performed theROSEexperimentsunderthesupervisionof WJ.YS.and S.hang prepared the DNAorigami samples under the supervisionof B.D.and W.J.,respectively.D.S.preparedthe expansionsamplesunder the supervisionof X.C.Wz.performedte simulationsandthetheoretical analysiswithcontributionsfromG.Q..H.J.W,R.C.andY.M.W.Z.analyzed thedata and prepared thefigures and videos with contributions from S. Zhao and L.L. B.-L.S. and J.X.provided some of the reagents and participated in someofthediscussions.Y.L.H.M.J.T.J.L.and B.-L.S.participatedin discussionsduring the development of the manuscript.L.C.H.L. and W.Z.wrote the manuscript with input from all authors.Alloftheauthors participatedindiscussionsand datainterpretation.

## Competing interests 

L.C., H.L., W.Z. and X.H.have a pending patent application on the presented framework.

## Additional information 

Extended datais availableforthispaperathttps://doi.org/10.1038/s41587-021-01092-2.Supplementary information The online version contains supplementary material available athttps://doi.org/10.1038/s41587-021-01092-2.



Correspondence and requests for materials should be addressed to Haoyu Li or Liangyi Chen.



PeerreviewinormioNtureocologytakstheaomousevrsortheir contribution to the peer review of this work.



Reprints and permissions information is available at www.nature.com/reprints.

<div style="text-align: center;"><img src="imgs/img_in_image_box_12_67_1176_579.jpg" alt="Image" width="97%" /></div>


<div style="text-align: center;">E deconvolution.Experiments were repeated ten times independently with similar results.Scale bars:1m. </div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_0_72_1152_1026.jpg" alt="Image" width="96%" /></div>


<div style="text-align: center;">Exte imaginniooflinallR,dtscom/2t/otrlin-).trmop bottom:head wlde.,eiarb),iaerba.fluorescencoillonlirstmlottl.WteRwaiteof1/4tD-,dSpar-M distinguished pair linesupto15m120m,and0m,respectively.WhentheNRwasintherangeof1/-1/16,D-IMand RL-Mail to recol lines up to 90 nm and 120 nm, respectively. </div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_22_69_1155_568.jpg" alt="Image" width="95%" /></div>


<div style="text-align: center;">E withr.ede Fg.).(Sparse-),rreolionlldbliackwttlionldcion.Teitiad TF ando)image.BeoreteSmaptimaiotetnitoTRFMand SpaIMimaereormaliedttheaeof1andthecoresponding residualmaea)iloced intof.agidin-e).Tclobtetclin) as magfd,lldl RL-deconvolution $(\mathsf{T I R F-S I M+R L\times}2)$ for3or 25iterations,or Fourier interpolated followed by the sparse deconvolution(Sparse-SIM×2).Experiments were repeated five times independently with similar results.Scale bars:(a-e)2m;(f)1m; (g)100nm. </div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_14_68_1186_1369.jpg" alt="Image" width="98%" /></div>


<div style="text-align: center;">Extended Data Fig. 4 | See next page for caption.</div>


Extended Data Fig.Rlative movements betwen sub-organllar structuresobserved bydual-color Sparse-IM.(a) Theinnerand outer mitochondrial membranes(OMMs and IMMs) labeled with Tom20-mCherry and Mito-Tracker Green in a liveCOS-7cell.(b) Magnified views from the whiteboxin (a).(c)Intensity profiles ofOMMs(magenta) andIMMs(cyan) along thecontinuous and dashed lines in(b),withmitochondrial configurationsshowninteiht.pare-IMreadilydetctedtotypeofOMMIMMsconguation:alongcistaextenddromone ideto2m awayfromteothersideoftheOMMandshortcitaextnddoly4mtowardsteothr sieoftheOMMs(upplementaryVido7).(d)Average FRC resolutions $(n=10)$ ).(e) The white dashed box in (a)is enlarged and shown at three time points.It revealed rare events: theIMMs extension not being enclosed withinthe Tom2-labeled structures inafew frames.This resultmight beexplained by thenon-homogenous distributionof Tom2protein ontheOMMs.(f) Arepresentative exampleofboththeIMMs(cyan) and ER(magenta,Sec61β-mCherry).As shown intheinse,we found that E tubulesrandomlycontacted themitochondriawithualprobabilityat boththecistaergionsandtheegionsbtwecristae.gMagfiedviewfrm thewhiteboxin).Wefound thatthecontactbetwenoneERtubuleandthetopofamitochondrion notonlycorrlated withthedirectional movmnt ofli%;whiskers,maximumand miimum;or bars,.e.m;Expeimntswreepatdfietimeindpndtlywthimilarslt.calebars:(a,1m; axial:0.2 arbitrary units (a.u.); lateral: 100nm; (b, e and g) 500 nm.



<div style="text-align: center;"><img src="imgs/img_in_image_box_5_65_1176_1151.jpg" alt="Image" width="98%" /></div>


<div style="text-align: center;">ExtendedDtag.Tee-imiolimaetackoflurcnt badsundIMandSpareI.b)Aaximumintitypjection (MIP)viewf)andhorionalctioni)ofluorctbadsmindiamt)rcordbD-()andartesparsedconvolution (b), respctil.intelwhowmad viwofteameflotbadudiftcotructiomos.) The correspondigGuidprofilina,lef-lwor),whicindiatettt lralWMofD-e)andSpre-blu)a 185nm (calibrated resolution-165nm) and 110 nm (calibrated resolution-90 nm), respectively (Supplementary Note 9.2).(d) Magnified horizontal sections from the white boxes in(a-b) are shown in the left and right panels,while the SD-SIMimage is processed with amedian filter to avoid a non-converedtedresult.)WeusedGaussianfunctionstofittheintnsityprofilealongtheaxialdirectionofthefluorscentbeadind),yildig axial resolutions of 484nm and 266 nm for SD-SIM and Sparse SD-SIM, respectively.(f) The gradually improved axial resolution(FWHM) of a 100nm bead while increasing the weight of sparsity.(g) Measuring the FWHM with fluorescent beads with a diameter of 45nm. The fitted FWHMs (cross-sections between white arrows displayed with white profiles in the right)of SD-SIM and Sparse SD-SIM are175nm and 92nm, respectively.As shown with yellow profiles(cross-sections between yellow arrows),the Sparse SD-SIM resolved adjacent two beads with a distance of 95nm.Experitsredetilimlalt.cler:)4mbinmnddfg)m.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_12_68_1178_1167.jpg" alt="Image" width="97%" /></div>


<div style="text-align: center;">Extended Data g.Dual-color live-ell imagingofclathrin and actin by Sparse D-SIM(Supplementary Video16).(ab) Colortemporal projections of CCPs(a) andthe actin filamentnetwork(b)recorded bySD-SIM(left) andSparseSD-SIM(right)for16.75minutes at5intervals.(c)CCPs(cyan)and thecortical actincytoskeleton(magenta)in aCOS-7cellcaptured by SparseSD-SIM.d)Montagesoftheboxed regionin(c)atfive-time pints are shown atamagnified scale;thefirstimaeobservedunderSD-SIMappars atthetopleftcornerforcomparison.Itcan beobservedthataCPdocks stably atthejunctiotwoactinfilametandtn diapparsomthefocalplaneathesenighborinfilamentmere.Experimentswererepated five times independently with similar results. Scale bars: (a-c) 4m; (d) 500nm. </div>


<div style="text-align: center;">Exten.cbe.ub)d li.a results.Scale bars: (a) 3μm; (b) 2m. </div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_0_70_1184_1475.jpg" alt="Image" width="99%" /></div>


<div style="text-align: center;">Extended Data Fig. 8 | See next page for caption.</div>


Extended Data Fig.8 Bona fide spatial resolution improvement of confocal and STED microscopes by the sparse deconvolution.(a) Nuclear pores in HeLa cells were labeled with an anti-Mab414 primary antibody and the Alexa594 secondary antibody, and observed under the Confocal, Sparse-Confocal,STED, and Sparse-STED configurations.(b) Magnified views from the region enclosed in the white dashed box in (a) under different microscopes.Huygens-represents that the images were deconvoluted by Huygens Professional (Scientific Volume Imaging, The Netherlands).(c) The Fourier transforms of images obtained by the corresponding microscopes. Labeled with the corresponding decorrelation resolution.(d) A representative HeLa cell in which microtubules (green) and mitochondria (magenta)were labeled with anti-tubulin and anti-Tom20 primary antibodies.It was imaged under the Confocal, Sparse-Confocal,STED, and Sparse-STED configurations.(e) Magnified views from the region enclosed by the white dashed box in (d).(f) Resolutions are masured b thedcorrlation mthod.S-Conocal:Spare-Confocal;SSTED:SparsSTD.Expeimnts ere repated ivetimes independently with similar results.Scale bars: (a, c,d) 2m; (b) 200nm; (e) 500 nm.



<div style="text-align: center;"><img src="imgs/img_in_image_box_14_73_1167_991.jpg" alt="Image" width="96%" /></div>


<div style="text-align: center;">Extended Data Fig.Extending the spatial resolution of aminiaturized two-photon microscope(MTM) with sparse deconvolution.(a)Three-imnoalditibutioofuronalditeandsisiiolumeof1m3fromthebaioThy-GFPtrannimuse were observed under the MTPM, and after RL (RL-MTPM)or the sparse deconvolution (Sparse-MTPM).Different focal planes away from the surface were color-coded and projected tooneimage(e Supplementary ideo1).(b-d) The x viwsand thir Fouriertransforms (a)under drentconfigurations (b, MTPM; c, RL-MTPM;d, Sparse-MTPM).(e) Magnified views from the region enclosed by the white box in (a)under different configurations (from left to right: MTPM, RL-MTPM,Sparse-MTPM).(f) Resolutions of designated configurations as calculated by the decorrelation method at different axial positions.Experiments were repeated five timesindependently with similar results.Scale bars: (a,d) 15m; (e)3m.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_19_67_1178_1320.jpg" alt="Image" width="97%" /></div>


<div style="text-align: center;">Extended Data Fig.10 |Highly-correlated $\mathsf{C a}^{2+}$ ·transients after the sparse deconvolution compared to the original data obtained by the SD-SiM.(a, b) The representative COS-7 cell was transfected with GCaMP6s, stimulated with ATP $\left(10\upmu M\right)$ .One snapshot under the SD-SIM(a) and after the sparse deconvolution (b) were shown.(c) Magnified views of regions enclosed by white boxes 1-4 in (a, and b).(d) ATP stimulated calcium traces from corresponding macrodomains in (c).(e) Representative ATP stimulated whole-cell calcium traces.(f) ATP stimulated increases in fluorescence intensities of GCaMP6s from different macrodomains (4 cell $\times4$ regions) under the SD-SIM (x-axis)exhibited a linear relationship with those obtained under the Sparse SD-SIM microscope (y-axis).(g) Average minimal resolutions by the FRC method $(n=10)$ ).Centerline,medians; limits, 75% and 25%; whiskers,maximum and minimum; error bars, s.e.m.Experiments were repeated five times independently with similar results.Scale bars: (a)5m; (c) 2m.</div>


# natureech 

## ReportingSummary 




<div style="text-align: center;"><html><body><table border="1"><thead><tr><td colspan="2"></td><td>For allstatiil analirm tttllowiimareprtin tue lend,tabl lendaixt,r Mhds ction.</td></tr></thead><tbody><tr><td>n/a</td><td>Confirmed</td><td></td></tr><tr><td></td><td></td><td>The exact sample size (n) for each experimentalgroup/condition,given as a discrete number and unit of measurement</td></tr><tr><td></td><td></td><td>A statement on whether measurements were taken from distinct samples or whether the same sample was measured repeatedly</td></tr><tr><td></td><td></td><td>The statistical test(s) used AND whether they are one-or two-sided Only commontests should bedescribedsolely byname;describe morecomplextechniquesinthe Methods section.</td></tr><tr><td></td><td></td><td>A description of all covariates tested</td></tr><tr><td></td><td></td><td>Adescription of any assumptions or corrections,such astests of normality and adjustment for multiple comparisons</td></tr><tr><td></td><td></td><td>Afull description ofthe statistical parameters including central tendency (e.g.means)orother basic estimates (e.g.regression coeficient) AND variation (e.g.standard deviation) or associated estimates of uncertainty (e.g.confidence intervals)</td></tr><tr><td></td><td></td><td>Frllc</td></tr><tr><td></td><td></td><td>Give P values as exact values whenever suitable. For Bayesian analysis,information on the choice of priors and Markov chain Monte Carlo settings</td></tr><tr><td></td><td></td><td>Forhlxiiofpdllioom</td></tr><tr><td></td><td></td><td>Estimates of effect sizes (e.g.Cohen'sd, Pearson's r),indicating how they were calculated</td></tr><tr><td></td><td></td><td>Our web collection on statistics for biologists contains articles on many ofthe points above.</td></tr></tbody></table></body></html></div>


## Statistics 

## Softwareandcode 

## Policy informationabout availabilityofcomputer code 


<div style="text-align: center;"><html><body><table border="1"><tr><td>Policy informationabout availabilityofcomputer code</td><td>Nocollected data,all data werecaptured byourownstructuredilluminationmicroscopy (SiM),spinning-disc confocal-based SiM(SD-SiM),</td></tr><tr><td>Data collection</td><td>stiml)ix-o microscope(MTPM),in whichthedetailscan befoundin the Methods section.The DNAorigamiwas designed using thecaDNAnov2.2.0.</td></tr><tr><td>Data analysis</td><td>The version of sparse deconvolution software used in this manuscript (accompanied with example data and user manual) is available as Suppleoilableirwis:// git./ https:///itt:// gith.l Nae.llIg, Mcl/ github.com/WeisongZhao/img2vid.</td></tr></table></body></html></div>


a 

## Data 

Policyinormioabouvlbi 

-Accesoulkubilbeaats - A list of figures that have associated raw data 

- A description of any restrictions on data availability 



Rawe findingsoetst.



## Field-specificreporting 

Pe.Life sciences Behavioural & social sciences Ecological,evolutionary & environmental sciences 

Fora referencecopyofthedocumentwithallsections,seenature.com/documents/nr-reporting-summary-flat.pdf 

## Lifesciencesstudydesign 

All studies must disclose on these points even when the disclosure is negative.

Sample size The sample size (n) of each experiment is provided in the figure/table legends in the main manuscript and supplementary information files.

Data exclusions No data was excluded from the analysis.

Replication The number of repetitions for each experiment is provided in the figure/table legends in the main manuscript and supplementary information files.



Randomization Samples were randomly assigned by independent persons.

Blinding Data acquisition and analysis were being blinded to the experimental groups.

## Reporting for specificmaterials, systemsand methods 

ereuireinformationromauthoraboutometpeomatrialsxeimentalytemandmehodsuedinmantudie.Here,inicatewhetherachmaterial,emic.

## Materials&experimental systems 

/a Involved in the study Antibodies 

Eukaryotic cell lines Palaeontology and archaeology Animals and other organisms Human research participants Clinical data Dual use research of concern 

Commercialimribie:ooclalbttilpaublin,bama2);oocloalouei-up107(Mab414),Abcam (ab24609); monoclonal mouse anti-Tom20,Tom20(29), BD Biosciences (612278); monoclonal rat anti-tubulin,YL 1/2. Abcam (ab6160).

seco;)

mcloli/g 

## ntibodies 

Antibodies used 

Validation 

## Methods 

n/a Involved in the study ChlP-seq Flow cytometry MRI-based neuroimaging  monocional mouse anti-Tom20, Tom20 (29), BD Biosciences (612278), https://doi.org/10.1038/s41467-021-22279-w;monoclonalratanti-tubulin,YL1/2,Abcam(ab6160),https:/doi.org/10.7554/eLife.61669;

## Eukaryotic cell lines 


<div style="text-align: center;"><html><body><table border="1"><thead><tr><td>Policy information about cell lines</td><td></td></tr></thead><tbody><tr><td>Cell line source(s)</td><td>INS 1 cells were kindly provided by Dr. lan Sweet, University of Washington Islet Core Facility (Sigma, SCC27) COS-7 cells were kindly provided by Professor Heping Cheng, Peking University (ATCC, CRL-151) HeLa cells were kindly provided by Professor Heping Cheng, Peking University (ATCC, CCL-2)</td></tr><tr><td>Authentication</td><td>Cell lines were not authenticated</td></tr><tr><td>Mycoplasma contamination</td><td>Cell lines were not tested for mycoplasma contamination.</td></tr><tr><td>Commonly misidentified lines (See ICLAC register)</td><td>No cell line listed by ICLAC was used.</td></tr></tbody></table></body></html></div>


## Animalsandotherorganisms 


<div style="text-align: center;"><html><body><table border="1"><tr><td colspan="2">olicyinoriEdmmdilr</td></tr><tr><td>Laboratory animals</td><td>Animals were housed with 12-h light/dark cycle at22C and free access to food and water.Amale 3-5months old Thy-1-GFP transgenic (C57BL6J) mouse was used.</td></tr><tr><td>Wild animals</td><td></td></tr><tr><td>We did not use any wild animals.</td><td></td></tr><tr><td>Field-collected samples</td><td>We did not use any field-collected samples.</td></tr></table></body></html></div>


te that full information on the approval of the study protocol must also be provided in the manuscript.