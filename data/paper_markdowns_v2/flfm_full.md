

Optics EXPRESS 

# Fourier light-field microscopy 

CHANGLIANG Guo, WENHaO LIu,1 XUANWE Hua, HaoYu L1,2AND SHU JIA,*



1The Wallace.oDarmto omcalin,GIittocologyand 

Emory University, Atlanta, GA 30332, USA 

2Ultra-PrecisionOptolctronicIntrument Engineering nte,HarbiIntituteof Technology, Harbi,

Heilongjiang, China 

3 These authors contributed equally to this work 

shu.jia@ gatech.edu 



Abstract: Observing the various anatomical and functional information that spans many spatiotemporal scales with high resolution provides deep understandings of the fundamentals of biological systems. Light-field microscopy (LFM) has recently emerged as a scanningfree, scalable method that allows for high-speed, volumetric imaging ranging from single-cell specimens to the mammalian brain. However, the prohibitive reconstruction artifacts and severe computational cost have thus far limited broader applications of LFM. To address the challenge, in this work, we report Fourier LFM (FLFM), a system that processes the light-field information through the Fourier domain. We established a complete theoretical and algorithmic framework that describes light propagation, image formation and system characterization of FLFM. Compared with conventional LFM, FLFM fundamentally mitigates the artifacts, allowing high-resolution imaging across a two- to three-fold extended depth. In addition, the system substantially reduces the reconstruction time by roughly two orders of magnitude. FLFM was validated by high-resolution, artifact-free imaging of various caliber and biological samples.Furthermore, we proposed a generic design principle for FLFM, as a highly scalable method to meet broader imaging needs across various spatial levels. We anticipate FLFM to be a particularly powerful tool for imaging diverse phenotypic and functional information, spanning broad molecular, cellular and tissue systems.


©2019 Optical Society of America under the terms of the OSA Open Access Publishing Agreement 

### 1. Introduction 

Light-field microscopy (LFM) simultaneously captures both the 2D spatial and 2D angular information of the incident light, allowing computational reconstruction of the full 3D volume of a specimen from a single camera frame [1–5]. Unlike other fluorescent imaging techniques that accumulate spatial information in a sequential or scanning fashion, this 4D imaging scheme effectively liberates volume acquisition time from the spatial scales (e.g.field of view (FOV) and spatialeiuklllelh-laging of biological systems with low photodamage across several spatial levels [5–9]. Towards the tissue level, the latest LFM techniques have demonstrated promising results for functional brain imaging with acellular-level spatial resolution of several micrometers across a depth of tens to hundreds of micrometers, and at a fast volume acquisition time on the order of 10 milliseconds [5–8].Atxodasmvructures and lillio,imaging depthof several micrometers tocover a sigfcat volumeof singleclls,and avolume acquisition time of millisecond [].

spatial and angular information, the recent development of wave-optics models allows for the reconstruction of densely aliased high-spatial requencies through point-spread function (PSF)deconvolution4,].However, to dat,therearetwo major imitations thatetictLMrom broader applications.First,thesampling paterofthe spatialinformationis uneven or LFM.Especially near the NIP, it becomes redundant, resulting in prohibitive reconstruction artifacts [4]. Existing LFM techniques mainly circumvent the problem by imaging on one side of the focal plane [4,5,7] or engineering the image formation or the wavefront [10–12], which, however,compromise either the imaging depth or resolution. Meanwhile, the focused plenoptic scheme has also been reported, which removes the artifacts near the NIP but may impair the refocusing (or volumetric imaging) capability due to the restricted sampling geometry of the angular information [13]. Alternatively, adefocused optical design has been proposed to rejectthe artifact region away from the FOV, recovering the image quality across the NIP [9]. However, the problem remains fundamentally unresolved. Second, the volumetric reconstruction employs PSF deconvolution using the wave-optics model [4,5]. The PSF of conventional LFM is spatially-varying in both the lateral and axial dimensions, thus described by a 5D matrix that projects the 3D object domain onto the 2D camera plane [4]. This aggravates the computational cost, making the reconstruction considerably slow and impractical for rapid observation of the dynamic or functional data. While several algorithms have been reported to accelerate the process [6,7], their applications are particularly limited to improve post-procesing of calcium imaing data ce           oe e current LFM techniques [14-16]. However, the initial works rely on the ray-optics integral model, thus compromising the image quality for high-resolution microscopy [14,15]. Another Fourier approach has lately been demonstrated for recording sparse neural activities in larva zebrafish with an extended FOV [16]. The work employed experimentally measured PSFs for reconstruction. However, the system lacks a complete algorithmic framework for modeling light propaatiandhahut bfllyexlored taiimum rrmance or diverse applications beyond calcium imaging. Hence, the advancement and generalization of the optical design and computational ramework of LFM for artifact-fre and fast light-ild imagig and reconstruction of broad volumetric data are still highly desirable.



Here, we intoduce Fourir lighld icrsopy (F) to achieve hih-quality imaging and rapid light-field reconstruction. By recording the 4D light field in the Fourier domain (FD), the imaging scheme transforms LFM in two main ways. First, the FD system allows allocating the spatial and angular information of theincident light in aconsistently aliased manner,effectively avoiding any artifacts due to redundancy. Second, because the FD processes the signals in a parallel fashion, image formation can thus be depicted by a unified 3D PSF, leading to substantially reduced computational cost by more than two orders of magnitude. The system was validated by high-resolution imaging and artifact-free reconstruction of various caliber and biological samples. In addition, we constructed a complete model for light propagation, image formation and reconstruction. Using this model, we established a generic design principle to facilitate any furher devlopmentof FLFM,a ahihly calable method t metbroader imaing needs across various spatial levels.



### 2. Methods 

#### 2.1. Experimental setup 

We constructed FLFM on an epifluorescence microscope (Nikon Eclipse Ti-U) using a 40x,0.95NA objective lens (Nikon CFI Plan Apochromat Lambda 40x, 0.95 NA) (Fig. 1(a)). The sample stage was controlled by a nano-positioning system (Prior). The samples were excited with either a 647-nm or a 561-nm laser (MPB). The corresponding emitted fluorescence was collected using a dichroic mirror and an emission filter (T660lpxr (Chroma) and ET700/75 (Chroma),and T560lpxr (Chroma) and FF02-617/73 (Semrock), respectively). The imaging area on the  NIP was adjusted by an iris (SM1D12, Thorlabs) to avoid overlapping light-field signals on the camera plane. A Fourier lens $\mathrm{FL},f_{\mathrm{FL}}=75or$ ·100 mm, Thorlabs) performed optical Fourier transform of the image at the NIP, forming a 4f system with the tube lens (TL). A microlens array (MLA, S600-f28, RPC photonics;$f_{MLA}=16.8mm;pitch=600\mu m)$ was placed at the back focal plane of the FL, thus conjugated to the back pupil of the objective. The light field was imaged using a 1:1 relay lens (Nikon AF-S VR Micro-Nikkor 105 mm f/2.8G IF-ED) and recorded on a scientific complementary metal-oxide-semiconductor (sCMOS) camera (Andor Zyla 4.2 PLUS sCMOS) at the back focal plane of the MLA.



<div style="text-align: center;"><img src="imgs/img_in_image_box_287_383_978_926.jpg" alt="Image" width="56%" /></div>


<div style="text-align: center;">Fig. 1. Fourier light-field microscopy (FLFM). (a) A schematic of the experimental setup forFLFM.Theobjective lnsOL)andthetube lens(TL)ormaimageattheaiimag plane (NIP), which areaisadjustdby aiis.TheFourier ens FL)ransform timage at the NIP to the back focal plane of the FL, where the microlens array (MLA) is situated.The light-field information is recorded by the sCMOS camera at the back focal plane of the MLA. DM, dichroic mirror; M, mirror. The inset diagram illustrates image formation through the MLA for emitters at different axial positions, implying recording of both the spatial and ulanormioiaucomomie ar.(,)3D rctivevw (b)and stack projection (c) of the simulated PSF through a 5×5 MLA (effective $\mathrm{p}\mathrm{itch}=89$ m in the object space) within an axial range from −40 m to 40 m. (d) The corresponding experimental PSF of the system across the same range, showing good agreement with the numerical model. The depth information in (c) and (d) is coded as shown in the color-scale bars. </div>


#### 2.2. Image formation and model for system characterization 

Image formation in the FLFM system is illustrated in the inset of Fig. 1(a) and described in detail in Appendices A-E. As seen, the light field from the image at the NIP is transformed to the FD by the FL, conjugated to the wavefront at the back pupil of the objective lens. The MLA segments the wavefront, thus transmitting the corresponding spatial frequencies (i.e. the angular information) after individual microlenses to form images in different regions on the camera.Using this scheme, the spatial and angular components can be recorded in an uncompromised and  well-aliased manner. This advantage results in image formation free of redundancy near the NIP and uniform across the depth of focus (DOF), permitting high-quality volumetric reconstruction without artifacts.



We developed the theoretical framework that integrates the complete set of FLFM parameters and thus allows for model-based system characterization (Appendices B-E). The model links the input parameters of FLFM such as the wavelength, NA, magnification, camera pixel and sensor size, and the focal length of the FL, with the system performance parameters, including the lateral $(R_{xy})$ and axial $(R_{z})$ solue, .u  ,using the FL of $f_{\mathrm{FL}}=75\mathrm{mm}$ 1, these system performance values can be obtained as $R_{x y}=2.12$ m,$R_{z}=4.70\mu\mathrm{m},F O V=67$ m and $DOF=64\mu m$ 1. The performance indicates high-resolution over a 2 to 3-fold extended depth, compared to conventional LFM using a similar objective [4,5].The model and its results were validated using various numerical and experimental methods as demonstrated in Section 3 and extended to generate a generic FLFM design principle in Section 4.



#### 2.3. Model of light-field propagation 

Projecting the 3D volume in the object domain to the 2D image space, the wavefunction at the NIP using the high-NA objective, is predicted by the Debye theory as [17]:

$$\begin{array}{c}{{U_{i}(x,\;p)=\frac{M}{f_{o b j}^{2}\lambda^{2}}e x p\left[-\frac{i u}{4s i n^{2}\left(\frac{\alpha}{2}\right)}\right]\times}}\\ {{\int_{0}^{\alpha}P(\theta)e x p\left[\frac{i u s i n^{2}(\theta/2)}{2s i n^{2}(\alpha/2)}\right]J_{0}\left[\frac{s i n(\theta)}{s i n(\alpha)}v\right]s i n(\theta)d\theta}}\end{array}$$

where $f_{o b j}$ is the focal length of the objective, and $J_{0}$ is the zeroth order Bessel function of the first kind. The variables v and u represent normalized radial and axial coordinates; the two variables are defined by $v=k[(x_{1}/M-p_{1})^{2}+(x_{2}/M-p_{2})^{2}]^{1/2}$ sin(α) and $u=4k p_{3}\mathrm{s i n}^{2}(\alpha/2)$ ;$p\:=\:(p_{1},p_{2},p_{3})\:\in\:\mathbb{R}^{3}$ is the position for a point source in a volume in the object domain;$\mathbf{x}=(x_{1},x_{2})\in\mathbb{R}^{2}$ represents the coordinates on the NIP; M is the magnification of the objective;the half-angle of the NA is $\alpha=\sin^{-1}(\mathrm{N A}/n)$ ; the wavenumber $k=2\pi n/\lambda$ were calculated using the emission wavelength λ and the refractive index n of the immersion medium. For Abbe-sine corrected objectives, the apodization function of the microscope $P(\theta)=\cos^{1/2}(\theta)$ was used.

T]Next, the image at the NIP,−$U_{i}(\mathbf{x},\mathbf{\mathfrak{p}})$ , is optically Fourier transformed onto the back focal plae .

of the $\mathrm{FL}$ ,, described as $O\mathcal{F}T[U_{i}(\mathbf{\boldsymbol{x}},\mathbf{\boldsymbol{p}})]$ , which is then modulated by the MLA, described using the transmission function $\phi(\mathbf{x}^{\prime})$ ,where $\mathbf{\bar{x}}^{\prime}=(x_{1}^{\prime},x_{2}^{\prime})\in\mathbb{R}^{2}$ represents the coordinates on the MLA.Specifically, the aperture of a microlens can be described as an amplitude mask rect $(\mathrm{x^{\prime}}/d_{\mathrm{M L A}})$ 1,combined with a phase mask exp $\begin{array}{r}{\left(\frac{-i k}{2f_{\mathrm{M L A}}}\left\|\mathbf{x}^{\prime}\right\|_{2}^{2}\right)}\end{array}$ . The modulation induced by a microlens is then described as:

$\phi\left(x^{\prime}\right)=r e c t\left(x^{\prime}/d_{M L A}\right)e x p\left(\frac{-i k}{2f_{M L A}}\left\|x^{\prime}\right\|_{2}^{2}\right)$ 

$$\phi\left(x^{\prime}\right)=r e c t\left(x^{\prime}/d_{M L A}\right)e x p\left(\frac{-i k}{2f_{M L A}}\left\|x^{\prime}\right\|_{2}^{2}\right)$$

where $f_{\mathrm{M L A}}$ is the focal length of the MLA, and $d_{\mathrm{M L A}}$ is the diameter of a single microlens (or the pitch of the MLA if the microlenses are tiled in a seamless manner). Thus, the modulation of the entire MLA, composed of periodic microlenses, can be described by convolving $\phi(\mathbf{x}^{\prime})$ 一with a 2D comb function c $\widehat{\mathrm{comb}(\mathrm{x}'/d_{\mathrm{MLA}})},\mathrm{i.e.}\Phi(\mathrm{x}')=\phi(\mathrm{x}')\otimes\mathrm{comb}(\mathrm{x}'/d_{\mathrm{MLA}})$ ,where is the convolution operator.T propagation over a distance of fMLA [18]:

$$h(x^{\prime\prime},p)=\mathcal{F}^{-1}\left\{\mathcal{F}[O\mathcal{F}T[U_{i}(x,\;p)]\varPhi(x^{\prime})]\times e x p\left[i2\pi f_{M L A}\sqrt{\left(\frac{1}{\lambda}\right)^{2}-(f_{x}^{2}+f_{y}^{2})}\right]\right\}$$

where $\mathbf{x}^{\prime\prime}=(x_{1}^{''},x_{2}^{''})\in\mathbb{R}^{2}$ represents the coordinates on the camera plane, the exponential term is teel o $f_{x}$ and $f_{y}$ ae $\mathcal{F}\{\}$ and $\mathcal{F}^{-1}\{\}$ ·represent the Fourier transform and inverse Fourier transform operators, respectively.$O\mathcal{F}T\{\}$ is the optical Fourier transform performed by the FL. In practice, the Fresnel propagation over the distance of $f_{MLA}$ is divided and calculated over steps for computational accuracy. The final intensity image $O(\mathbf{x}^{\prime\prime})$ at the camera plane is described by:

$$\begin{array}{r}{O(x^{\prime\prime})=\int^{|h(x^{\prime\prime},p)|^{2}}g(p)d p}\end{array}$$

where $\mathbf{p}\in\mathbb{R}^{3}$ , as defined in Eq. (1), is the position in a volume containing isotropic emitters,whose combined intensities are distributed according to $g(\mathbf{\mathfrak{p}})$ 



Using this model, the light-field propagation in FLFM at varying depths was demonstrated (Figs. 1(b) and 1(c)) and compared with the experimental data acquired by recording 200-nm fluorescent beads (T7280, ThermoFisher) at the same depths (Fig. 1(d)). As seen, the numerical and experimental data agreed well across the entire DOF and exhibited several unique features of the system. First, like conventional telecentric microscopes, the lateral translation of an emitter provides no parallax of images formed by each individual microlens. Second, unlike the orthographic views produced by conventional microscopes, different axial depths lead to variations of the wavefront (i.e. composite spatial frequencies) at the back pupil. This axial information is coupled to the lateral displacement and recorded in a radially asymmetric manner (except for the microlens centered at the optical axis). Therefore, such paralleled recording of signals in the FD allows describing the imaging system using a unified 3D PSF (e.g. Figs. 1(b)−1(d)), rather than a five-dimensional matrix as in the conventional, spatially-varying LFM system. This provides superb computational benefit in the reconstruction process.



Furthermore, the model is fully compatible with various modules for phase variations (e.g.PSF engineering [10], aberrations, customized MLA, etc.) to accurately describe the actual performance of the FLFM system. In addition, such a complete framework of light propagation enables the reconstruction of those volumetric data, where experimentally measured PSFs may not be readily available [16], such as in intact, dynamic, or time-evolving biological samples.

#### 2.4. Reconstruction algorithm 

Mathematically, the reconstruction is an inverse problem to recover the radiant intensity at each point in the 3D volume, denoted by g, using the camera image O.They satisfy the relationship $O=H g$ _, where the measurement matrix H is determined by the PSF, and its elements $h_{j,k}$ represent the projection of the light arriving at pixel $O(j)$ on the camera from the kth calculated volume $g^{(k)}$ in the object space. To obtain g, the inverse problem thus becomes:

$$g^{(k+1)}=d i a g[d i a g{(H^{T}H g^{(k)})}^{-1}(H^{T}O)]g^{(k)}5
$$

where the operator diag{} diagonalizes a matrix. This expression is a modified deconvolution algorithm based on the Richardson-Lucy iteration scheme[19,20]. Inour case, the sampling intervals for the reconstruction of the object space are given as $\Delta_{xy}=0.943\mu m,\quad and\quad\Delta_z=0.5\mu m$ |.EM 

The 3D deconvolution conducts forward projection $$ and backward projection $(H^{T}\dot{O}$ and $H^{T}Hg^{(k)}$ iteratively between the 3D object space and the 2D camera plane. Furthermore,because of the spatially-invariant nature, the 3D PSF for reconstruction can be simplified to $\mathrm{P S F}(\mathbf{x}^{\prime\prime},z)=|h(\mathbf{\hat{x}}^{\prime\prime},\mathbf{p})|^{2}$ , where the PSF can be described by an emitter located on the optical axis,i.e.$\mathbf{p}=(0,0,z)$ . As a result, the forward projection can be described as a sum of 2D convolution layer by layer for an axial range of [zo, z1], i.e.$\begin{array}{r}{H g^{(k)}=\sum_{z=z_{0}}^{z=z_{1}}\mathrm{P S F}(\mathbf{x}^{\prime\prime},z)\otimes g^{(k)}(z)}\end{array}$ , where $g^{(k)}(z)$ relates to the single layer of the 3D object located at the depth of z. The back projection can thus be given as.$\bar{[H^{T}O](z)}=\mathrm{P S F}(\mathrm{x}^{\prime\prime},z)\otimes\mathrm{O}\mathrm{a n d}[H^{T}H g^{(k)}](z)=\mathrm{P S F}^{\prime}(\mathrm{x}^{\prime\prime},z)\otimes H g^{(k)}$ , where $\mathtt{P S F}^{\prime}(\mathbf{x}^{\prime\prime},z)$ 

is obtained by rotating $\mathtt{P S F}(\mathbf{x}^{\prime\prime},z)$ by 180 degrees. As seen, the simplified computational scheme using the unified 3D PSF effectively reduces the dimensions of the deconvolution algorithm,allowing for substantial reduction of the reconstructiontime by orders of magnitude. Furthermore,due to the viable alignment of the sytem andconsistency betwenthe numerical and experimental PSFs, no image registration and matching have been considered in the reconstruction process,which, however, can be employed to further improve the image quality. An algorithm flow chart has been provided in Appendix F (Fig. 14) for readers' information and the code is available from the corresponding author upon request.



### 3. Results 

#### 3.1. Imaging caliber structures 

Using the 647-nm laser, we first imaged sub-diffraction-limit 200-nm dark-red fluorescent beads (T7280, ThermoFisher) and measured the 3D reconstructed images at varying depths (Fig. 2(a).The full-width at half-maximum (FWHM) values of these reconstructed images at each depth were ~2 m and ~4–5 m in the lateral and axial dimensions, respectively, consistent with the theoretical values of 2.12 m and 4.70 m (Section 2.2, Appendices B and C), respectively.Furthermore, two beads separated by 2.90 m can be resolved using FLFM, in good agreement with the FWHM values (Fig. 2(b)). It should be noted that the wave-optics model of FLFM allows for high-resolution reconstruction through PSF deconvolution. In contrast, the conventional ray-opticsedial odl ot pvie ufiitlutio[14, Fig.2(b)).

Next, we imaged surface-stained, 6-mfuorescent microspheres (F14807, ThermoFisher),which hollow structure wasclearly resolved using FLFM (top row,Fig.2(c)).The corresponding lateral and axial cross-sectional profiles exhibited the FWHM values of the stained surface at 1–2m and 2–4 m in the latral and axial dimensions, respectively, consistent with the theoretical values and experimental measurements in Fig. 2a. Notably, the structure of the microsphere revealed by FLFM agred well with our numerical results (Appendix G).We further analyzed in Appenixofoiic crosllbjustin $f_{\mathrm{F L}}$ ,the focal length of the FL.公司E 

For comparison, we reconstructed the same structure using the integral imaging model which was, however, poorly resolved due to the limited 3D resolution (middle row, Fig. 2(c)).Furthermore, we imaged the microsphere using conventional LFM, i.e. by placing the MLA (MLA-S125-f30, RPC photonics;$f_{\mathrm{MLA}}=3.75\ \mathrm{mm};\ \mathrm{pitch}=125\ \mu\mathrm{m}$ )on the NIP (bottom row,Fig.2(c)).However,prohibitiveartifacts havebeenobservednearthe NIP and extending into a significant ageof theOF.Ithisase,hesult howed ubstaially dgradedvolumetric imaging capability, unable to display the structure in the lateral dimension and leading to erroneously reconstructed patterns in the axial dimension.TG 

Using ,  d d d -mt   3D space (Fig. 2(d)). Four emitters located at different depths of $-28~\upmu\mathrm{m},-22~\upmu\mathrm{m},-9$ μm and -5 m were reconstructed from one camera frame without the need for axial scanning,compared to wide-field microscopy. Lastly, we tracked the movement of 200-nm fluorescent beads suspended in water at various volume acquisition rates of 10 ms (Fig. 2(e) and Visualization 1), 40 ms (Visualization 2) and 100 ms (Visualization 3). The 3D positions and trajectories of the particles were determined by localizing the reconstructed particles using Gaussian fi tting with nanometer-level precision in all three dimensions. The measurements of the reconstructed particles are consistent with the values as in Fig. 2(a), showing no compromise in spatial precision as the volume acquisition rate is varied.



<div style="text-align: center;"><img src="imgs/img_in_image_box_157_141_1075_594.jpg" alt="Image" width="75%" /></div>


<div style="text-align: center;">Fig. 2. Characterization of FLFM and imaging caliber samples. (a) Left panel, 3D view of a reconstructed 20-nm ffluorescent bead using the MATLAB function isosurface'. Right pl $y-z$ ,and -z across the center of the bead, exhibiting FWHM values of 1.98 m, 2.07 m, and 4.39min ly.))awF)o fluorescentbadslcatedotheocallaeTheiti)howstheoomediimae of theboxedrgion.Aconstucted axial stackof(i)using wave-optics dconvoluion (i) ndy-gli).)owm-ia )inra (iv), respectively. FLFM with the wave-optics model has been shown to resolve two beads separated by 2.90 m, confirmed by theinset in (). c) The reconstructed cross-sectional images (left panel) and profiles along the dashed lines (right panel) of a surface-stained 6-m fluorescent bead using FLFM with the wave-optics (top row) and ray-optics (middle row) models. The hollow structure was clearly observed using the wave-optics model,while the ray-optics model failed to provide sufficient resolution. The same sample was also imaged using conventional LFM (bottom row) near the NIP, where strong artifacts prohibited proper visualization of lateral and axial structures. (d) Raw light-field (top)and reconstructed 3D FLFM (bottom) images of 200-nm fluorescent beads distributed in a volume. The reconstructed axial positions of four beads were identified at −28 m,$-22$ m, −9 m and −5m. The dashed lines in the raw image represent the edges of the square-shaped microlens.) Top ,3Dconstruct rjectoiesof 2-mfluorescent beads suspended in water and axially searated $\mathrm{b y}>30\upmu\mathrm{m}$ ,tracked at a volume acquisition time of 100 ms (se Visualization 1). Top right, oomed-in 3D trajectory of thecorresponding boxediita.,oi $x-y$ , -z, and y-z.Different time-points are linearly color-coded from 0 to 4 s. The FLs of $f_{\mathrm{F L}}=75$ mm (a, c,d) and $f_{FL}=100$ mm (b, e) were employed. Scale bars: 2 m (a, b (i, v, vi)), 5 m (c), 20m (b (ii), d), 10 m (b (iii, iv), e). </div>


#### 3.2. Imaging biological samples 

We then demonstrated FLFM by imaging mixed pollen grains stained with hematoxylin and phloxine B (304264, Carolina Biological Supply) using the 561-nm laser (Fig. 3). As seen, the raw data behind individual $3\times3$ microlenses have revealed different perspective views of the sample (Fig. 3(a)). The system captured a $\mathrm{FOV>}67\times67$ μm and allows to reconstruct across a $\mathbf{DOF}>50$ m, enclosing the entire pollen, at a volume acquisition time of 0.1 s. The full  4D light-field information recorded by a single camera frame consents to synthesize the focal stacks of the full volume of the specimen (Figs. 3(b) and 3(c)). Remarkably, FLFM recovered the structures that were out-of-focus and poorly sectioned by wide-field microscopy (e.g. insets in Fig. 3(c)). The high spatial resolution allows us to visualize the fine spine structures of the pollen that exhibited FWHM values of ~1−2 m in width and of ~5 m in length, and were separated as close as a few micrometers in all three dimensions (Figs. 3(c) and 3(d)). It should be mentioned that these measured system parameters are consistent with our theoretical predictions in Section 2.2, and the use of denoising or thresholding strategies should further improve the crosstalk between the axial stacks due to the limited axial resolution and the overlapping 3D data during projection onto the 2D camera sensor.



<div style="text-align: center;"><img src="imgs/img_in_image_box_166_426_1045_983.jpg" alt="Image" width="71%" /></div>


<div style="text-align: center;">Fig. 3. Imaging pollen grains using FLFM. (a,b) Raw light-field (a) and reconstructed 3D FLFM (b) images of a pollen grain stained with hematoxylin and phloxine B. The spines of the pollen oriented into three dimensions can be observed in (b). The depth information across a 50-m range in (b) is color-coded according to the color scale bar. (c) Selected z-stack images. The insets show the zoomed-in FLFM (left) and wide-field (right) images at $z=2$ umof twospines (both are $12.03\times12.03$ m), respectively. The results show sensitive axial discrimination and 3D resolution of the pollen structure using FLFM. (d)Corresponding cross-sectional profiles along the dashed line in (c) at $z=2$ m. The profiles exhibited two spines separated by ~4 m and their FWHM values of 1–2 m resolved by FLFM. Scale bars: 20 m (a), 10 m (b, c). </div>


Next, we imaged mouse kidney tissue slice (F24630, ThermoFisher) using the 561-nm laser,where the filamentous actins, prevalent in glomeruli and the brush border, were stained with Alexa Fluor 568 phalloidin (Fig. 4 and Visualization 4).  FLFM recorded the 4D light-field information of the proximal tubule brush border (Fig. 4(a)) and allows to reconstruct the entire thickness of the tissue slice (~20 m) from one camera frame (Fig. 4(b)). In the reconstructed image, the pattern of proximal tubules and brush borders can be well visualized in all three dimensions. It is also noticed that the apical domain of the brush border of the tubules exhibited  brighter stain, as known due to the denser distribution of actin bundles. Compared to wide-field microscopy, FLFM is capable of capturing the volumetric signals from a single camera frame and recovering synthesized axial stacks. The high resolution and sectioning capability of FLFM allow visualizing finer 3D structural variations (Figs. 4(c) and 4(d)). Tubular structures of a few micrometers across the DOF in all thre dimensions can be well resolved (Figs. 4(c)–4(f)).

<div style="text-align: center;"><img src="imgs/img_in_image_box_251_290_1072_901.jpg" alt="Image" width="67%" /></div>


<div style="text-align: center;">Fig. 4. Imaging mouse kidney tisue using FLFM (see Visualization 4). (a,b) Raw light-field (a) and reconstructed 3D FLFM (b) images of a cryostat section of mouse kidney stained with Alexa Fluor 568 phalloidin using a 75-mm Fourier lens. The inset in (b) shows the cross-sectional view in -z of the corresponding layer marked in (b). The color represents intensity levels in (b). (c, d) Axial-stack images of the reconstructed volume by FLFM (c) and by scanning wide-field microscopy (d). The arrows indicate the enhanced signals and sectioning capability of FLFM that reveal fine 3D structural changes. The grids in the images are the edges of the microlenses when acquiring the corresponding wide-field images through the MLA. (e) The cross-sectional profile along the axial dimension of the region as marked in (b), exhibiting a FWHM valueof 4.75 m.f) Thecross-ctional profile along the dashed line in (c), exhibiting resolved filaments at $z{=}{-}1.5$ m separated by 3.3 m. Scale bars: 20 μm. </div>


Lastly, it should be addressed that for all the above imaging tasks, we used standard GPU calculation on a desktop computer (Intel(R) CPU i7-6850K (3.60 GHz), 128GB RAM, NVIDIA GeForce GTX1080Ti (Default/Turbo Clock 1480.5/1582MHz)). For example, conventional LFM typically takes an average of 31 s per deconvolution iteration to reconstruct a volume of $67\times67$ $\times30$ umwith avoxel size of $0.943\times0.943\times0.5$ μm from a single camera frame of $210\times210$ pixels. As a comparison, FLFM utilizes an average of 0.34 s per iteration for an image of the same size, representing a roughly two orders of maggnitude of improvement in computational cost (both methods use a similar total of 10–100 iterations for reconstruction). The reconstruction speed can be further accelerated using cluster computing and advanced deconvolution algorithms.

The scheme has herby paved the way  ulimatly vercomin the spatio-temporal-limiting step for live imaging and rapid video-rate reconstruction.



### 4. General design principle of FLFM 

In this work, we have established the complete theoretical and algorithmic framework underlying light propagation, image formation and system characterization of FLFM. Here, we further derived this framework into a general design principle for FLFM, essential for advancing the highly scalable approach to meet broader imaging needs across various spatial levels.

As seen in Fig. 1(a), as well as the top panel in Table 1, the FLFM system is composed of two main modules, the original wide-field imaging module including the camera, and the light-field module including the FL and the MLA. Given a standard wide-field system, to design a FLFM system is inherently to identify the parameters for the light-field module.

<div style="text-align: center;">Table 1. Design principle of FLFM.</div>



<div style="text-align: center;"><html><body><table border="1"><tr><td colspan="7">d1 dMLA $D_{\mathrm{pupi}}$ $D_{\mathrm{pupil}}$ $f_{1}\quad f_{n}\quad f_{n}$ $d_{max}$</td></tr><tr><td colspan="2">Category I Category II Category III Input Parameters Performance Parameters Design Parameters</td><td colspan="4"></td></tr><tr><td colspan="2">λ NA M P FOV DOF fFL N $D_{\mathrm{am}}$ $s_{r}$ $\pmb{R}_{z}$ $R_{x y}$ $M_{T}$ $d_{MLA}$ $\mathbf{f}_{\mathrm{M L A}}$ $d_{1}\setminus d_{\max}$</td><td colspan="3">λ NA M P $D_{\mathrm{am}}$</td><td colspan="2">fFL N $d_{MLA}$ $\mathbf{f}_{\mathrm{M L A}}$ $d_{1}\setminus d_{\max}$</td></tr><tr><td colspan="2"></td><td colspan="3"></td><td colspan="2"></td></tr><tr><td rowspan="2">Performance Parameters</td><td>$d_{MLA}R_{xy}{}^2$ $R_{z}$ $\lambda d_{max}$</td><td colspan="3">$R_{z}$</td><td colspan="2">DOF</td></tr><tr><td>Y $2\left(4+\frac{2}{{{s_{r}}}}\right){R_{x y}}^{2}$</td><td colspan="3">$\frac{S_{r}P}{R_{xy}}$</td><td colspan="2"></td></tr><tr><td rowspan="2">Design Parameters</td><td>$f_{F L}$</td><td>$N$</td><td>$d_{MLA}$</td><td>$f_{M L A}$</td><td>$d_{1}$</td><td>$d_{max}$</td></tr><tr><td>$D_{cam}\times M$ $\overline{{2N A}}$</td><td>$R_{xy}\frac{2NA}{\lambda}$</td><td>$\frac{D_{cm}}{N}$</td><td>$S_{r}Pf_{FL}$ $\overline{{R_{x y}M}}$</td><td>$F O V\frac{M f_{M L A}}{f_{F L}}$</td><td>$\begin{array}{r}{d_{1}\times\left\lfloor\frac{D_{c a m}-d_{M L A}}{2d_{1}}\right\rfloor{}^{(*)}}\end{array}$</td></tr></table></body></html></div>


First, we summarized the complete set of FLFM parameters, which can be organized into three categories: 1) the input parameters of the wide-field imaging module, including the emission wavelength λ, the numerical aperture NA and the magnification M of the objective, and the camera pixel size P and the physical size of the sensor $D_{\mathrm{c a m}};2)$ )the performance parameters ofe $R_{xy}$ and $R_{z}$ pixel sampling rate $S_{r}$ (i.e. the ratio between $R_{x y}$ and the effective pixel size $P/M_{\mathrm{T}}$ ,where $M_{\mathrm{T}}$ is the magnification of the FLFM system), FOV, and DOF; 3) the design parameters to describe the light-lof $f_{\mathrm{F L}}$ , the diameter of the microlens $d_{MLA}$ , the occupancy ratio N (i.e. the ratio between the effective pupil size at the MLA $D_{\mathrm{pupil}}$ and $d_{MLA}$ 1, the focal length of the microlens $f_{\mathrm{M L A}}$ , the pitch of the MLA $d_{1}$ , and the distance from the outmost microlens covered by the illumination beam to the center of the MLA $d_{\max}$ . It should be mentioned that we here considered hexagonal MLAs (e.g. the right in top panel of Table 1) for the best radial symmetry and dense packing to gain optimum light-field reconstruction, although the strategy is applicable to various MLA patterns. The goal of the design is thus to identify the design parameters in the third category.

Next, we derived theoretical relationships between these parameters as an inverse problem based on themodelof systemcharacterization developedin Section2.B.As listedinTablan derived in Appendix H, the design parameters can be determined using these relationships with the input and performance parameters. Specifically, the input parameters are usually provided for the wide-field imaging system, while the developers can decide on the desired performance parameters of FLFM. It should be noted that the identification of the proper performance and design parameters can be iterative due to their interdependent relationships (e.g. lateral and axial resolution $R_{xy}$ and $R_{z}$ are intrinsically connected with $d_{\mathrm{M L A}}\;\mathrm{a n d}\;d_{\mathrm{m a x}})$ . In practice, only three independent performance parameters such as $R_{x y},S_{r},F O V$ are initially required in order to determine all the design parameters and the rest of the performance parameters. The developers can then adjust the initial values and iterate the process to obtain an optimum combination of elements to satisfy the imaging need.



As an illustration, we can customize the performance of the FLFM system reported in this work using this design protocol. First, the input parameters are given as $\lambda=680nm,NA=0.95,M=40$ $P=6.5\mu m$ 1, and $D_{\mathrm{c a m}}=13.3$ mm. Next, our desired performance, for instance, is to achieve a 3D resolution of ${\sim}2{-}3$ m, a large $\mathrm{FOV}>500$ m, and a $\mathrm{DOF}>50$ m for a specific imaging need. We first set $D_{\mathrm{p u p i l}}$ equal to $D_{\mathrm{c a m}}=13.3$ mm for the maximum use of the camera sensor.Then, using the model, we can generate various combinations of the performance parameters that meet the requirement. One set of such parameters could be $R_{x y}=2.14~\mu\mathrm{m},R_{z}=2.79$ m,$S_{r}=1.56,M_{\mathrm{T}}=4.74,FOV=561\ \mu\mathrm{m}$ 1, and $DOF=71.2\mu m$ 1. Hence, the design parameters for the light-field module can be obtained as $f_{\mathrm{F L}}=280$ mm,$d_{\mathrm{MLA}}=2.2\mathrm{~mm},\quad N=6,f_{\mathrm{MLA}}=33.2\mathrm{~mm}$ ,$d_{1}=2.66\ mm$ ,and $d_{\max}=5.32\ mm$ 



### 5. Conclusion 

In summary, we have developed FLFM to achieve high-quality light-field imaging and rapid volumetric reconstruction. Imaging the light field in the FD fundamentally mitigates the prohibitive artifacts, providing two-to thre-fold larger DOF than the previous LFM design.The design also substantially reduces the computational cost by more than two orders of magnitude. We have established the theoretical and algorithmic models to describe the system and dmd-l,aofoudlol m.Furthermore, the work provided a generic design principle for constructing and customizing FLFM to address broad imaging needs at various spatial scales.The stud ha come e to ma ima i e cu F mho a m advance new imaging physics and applications for LFM and MLA-facilitated microscopy. The advancements in both imaging capability and computation speed promise further development toward high-resolution, volumetric data acquisition, analysis and observation at the video rate and ultimately in real time. Combining molecular specificity, great scalability, engineered MLAs and advanced computing, we anticipate FLFM to be a particularly powerful tool for imaging diverse phenotprllue stems.

## Appendix A: Image formation in traditional LFM and FLFM 

Here, we demonstrated both the numerical and experimental data for light propagation (Figs.5and 6) for traditional LFM and FLFM. We also provided the corresponding imagge formation for traditional LFM (Fig. 7), compared to the result in Fig. 2(a).



<div style="text-align: center;"><img src="imgs/img_in_image_box_331_156_911_623.jpg" alt="Image" width="47%" /></div>


<div style="text-align: center;">Fig. 5. Experimental setup and light propagation for traditional LFM (top) and FLFM (bottom) using a 40x, 0.95NAobjctive lns. Theinsets on the riht sho thecorresponding light-field images on the camera. NOP, native object plane; OL, objective lens; TL, tube lens; NIP, native image plane; FL, Fourier lens; CP, camera plane.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_166_788_1050_948.jpg" alt="Image" width="72%" /></div>


<div style="text-align: center;">Fig. 6. x-z view of the PSFs across the central row of microlenses for FLFM (left panel)and traditional LFM (right panel). Numerical (top panel) and experimental (bottom panel)results show good agreement. The dashed lines represent the NIP and the redundantly aliased region can be observed in the PSF of traditional LFM. The experimental results show background noised due to less sufficient SNRs. Scale bars: 10 m.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_155_1137_1052_1348.jpg" alt="Image" width="73%" /></div>


<div style="text-align: center;">Fig.7. Left to right, raw light-field data, reconstructed 3D image,cross-sectional images at the NIP and the corresponding profiles of the 200-nm fluorescent bead located on the native object plane using traditional LFM. Compared to the result in Fig. 2(a), severe reconstruction artifacts can be observed for traditional LFM near the NIP. </div>


## Appendix B: Lateral resolution

The lateral resolution $R_{x y}$ ily aperture (NA) of the microlens and the diffraction-limited spot size on the sCMOS camera, to determine the final resolution of the FLFM system. Here, we first considered a point emitter in the object space, which is then imaged to the native image plane (NIP) through the wide-field microscopy system $(M=40\times,\mathrm{NA}=0.95)$ ), followed by Fourier transform to the Fourier domain (FD) at the back focal plane of the Fourier lens (FL). The beam in the FD can be considered as collimated when the image of the point emitter is located on the NIP. According to the Abbe diffraction limit of the microlens, the beam spot on the sCMOS camera after each microlens is given as $\frac{\lambda}{2N A_{\mathrm{M L}}}$ ,where $NA_{ML}$ is the NA of each microlens, λ is the wavelength of the emission.This defines the lateral resolution of the images from two emitters on the NIP. Converting to the object space, the lateral resolution of the whole system can be determined by this diffraction limit of the microlens, given as $R_{xy}=\frac{\lambda}{2NA_{ML}}\times\frac{f_{FL}}{f_{MLA}}\times\frac{1}{M}=\frac{\lambda N}{2NA}$ . Here, the paraxial approximation permits $2N A_{\mathrm{M L}}f_{\mathrm{M L A}}=d_{\mathrm{M L A}}$ .For example, given the parameter values of $f_{\mathrm{F L}}=75\mathrm{m m}$ and $d_{\mathrm{M L A}}=600\upmu\mathrm{m},N=5.9375$ in our system. The lateral resolution is thus given as $R_{x y}=2.12$ m. As seen from the expression, the lateral resolution can be improved by enlarging dMLA or reducing fL. In addition, we validated the calculated lateral resolution by simulating PSF distributions using the wave-optics model for light propagation as described in Section 2.3 of the main text.We simulated the lihtfildof pointemitter at varying depths andreconstructed their images. As seen, the FWHM values of the reconstructed images increase (i.e. the lateral resolution becomes worse) when the emitter is moved further away from the focal plane (Fig. 9).

$$R=\frac{\lambda}{2NA_{ML}}$$

<div style="text-align: center;">Fig.8. Analysisof the lateral resolutionof FLFM.The figure shows the model of light propagation, image formation and symbols to determine the lateral resolution.</div>


<div style="text-align: center;"><img src="imgs/img_in_chart_box_283_161_954_581.jpg" alt="Image" width="54%" /></div>


<div style="text-align: center;">Fig. 9. Numerical study of the FWHM values of the reconstructed images of a point emitter in all three dimensions, as a function of axial positions from −20 m to 20 m. 5 iterations were used for deconvolution, consistent with Fig. 2(a). </div>


## Appendix C: Axial resolution

We utilizedtheorticl and umercal modltanalyze h axial resolution $R_{z}$ in this section.As shown in Fig. 10 (a), we considered two patterns on the camera plane, generated respectively from two emitters located at different axial positions on the optical axis. We reasoned that if the elemental images of these two patterns after the outmost microlenses, described as $(-1$ $-1),\:(-1,\:1),\:(1,\:-1)$ , and (1, 1) (top right panel, Fig. 10 (a)), can be resolved (i.e. by the diffraction limit of $\frac{\lambda}{2N A_{\mathrm{M L}}}$ of each microlens), the axial positions of the two emitters can be resolved through the reconstruction process. We assume that the PSF experiences negligible change within the axial range of interest, i.e. maintaining the width of $\overset{\rightharpoonup}{\frac{\not{2}NA_{ML}}{}}$ ·. In this sense,the axial resolution can be calculated from ray optics directly. In our case, it is given as $R_{z}=\frac{\lambda}{2NA_{\mathrm{ML}}}\times\frac{f_{\mathrm{FL}}}{f_{\mathrm{MLA}}}\times\frac{1}{\tan(\theta')}\times\frac{1}{M^{2}}=\frac{\lambda N^{2}}{4\sqrt{2}NA^{2}NA_{\mathrm{obj}}^{2}}$ , where tan $\begin{array}{r}{(\theta^{\prime})=\frac{\sqrt{2}d_{\mathrm{M L A}}}{f_{\mathrm{F L}}}}\end{array}$ and $2N A_{\mathrm{M L}}f_{\mathrm{M L A}}=d_{\mathrm{M L A}}$ based on the paraxial approximation. Plugging the system parameters, we obtain the axial resolution $R_{z}=4.7$ m.



We assessed the theoretical axial resolution by simulating the PSF using our wave-optics model for light propagation as described in Section 2.3 of the main text (Figs. 10(b) and 10(c)). We first simulated light propagation in the 3D space (Fig. 10(b)), where the lateral displacement of the PSF generated by the $(-1,1)$ ) microlens as a function of the axial position can be identified by Gaussian fitting of the beam profile (Fig. 10(c)). The fitted curve exhibited a linear relationship and the slope was calculated as $p=0.2763$ ,indicating that one-pixel change in the z direction leads to a shift of 0.2763 pixel in the $\mathbf{x}\mathbf{-y}$ plane. In practice, as mentioned in Section 2.4, the pixel size in the $\mathbf{x}-\mathbf{y}$ plane in object space is $\Delta_{x y}=0.943$ m, and the pixel size in z is $\Delta_{z}=0.5$ m. The axial resolution can thus be determined as $\begin{array}{r}{R_{z}=\frac{R_{x y}}{p\times\Delta_{x y}}\times\Delta_{z}=4.1}\end{array}$ m, consistent with the above theoretical value of 4.7 μm.



Next, we performed another numerical study to verify the axial resolution (Fig. 11). We studied two axially separated point emitters at (4 m and 0 m), (2 m and −2μm), and (0 m and −4 m), respectively. In Fig. 11, the left panel shows the raw light field images generated by the two point emitters at different depths; the middle panel shows the 3D reconstructed emitters and their perspective and axial views; the right panel shows the profiles of the emitters along the dashed lines in the axial images. As seen, these emitters separated by 4 μm at varying depths can 

<div style="text-align: center;">(a)</div>


<div style="text-align: center;">Fig. 10. Analysis of the axial resolution of FLFM. (a) Left, the model and symbols to determine the axial resolution. Right, symbols and indices of the corresponding microlenses.(b) Simulated light propagation and identificationof axial distributions of the PSF after microlenses. Scale bar: 20 m. </div>


be resolved. In practice, due to the noise and other system imperfections, the axial resolution in our experiments was validated closed to 5 m, still consistent with the theoretical value of 4.7 m. Like the lateral resolution, the axial resolution also varies along the axial dimension as shown in Fig. 9. As seen, the axial FWHM values increase from ~5 m to 10 m when the emitter is moved from the focal plane to 20 m away from the plane.

<div style="text-align: center;"><img src="imgs/img_in_image_box_297_153_899_682.jpg" alt="Image" width="49%" /></div>


<div style="text-align: center;">Fig. 11. Analysis of the axial resolution of FLFM by reconstructing two axially separated point emitters. Scale bars: 20 m (left panel), 2 m (middle panel).</div>


## Appendix D: Field of view (FOv)

The FOV around the focal position in the object space can be identified from the model shown in Fig. 12. As seen, the FOV is determined by the image area after each individual microlens.Therefore, the FOV depends on the size and focal length of the microlens and the focal length of the FL, given as $\bar{FOV}=d_{MLA}\times\frac{f_{FL}}{f_{MLA}}\times\frac{1}{M}$ Using our system parameters, the value is givenas $\mathrm{FOV}=66.96$ m. In addition, the FOV can be customized by adjusting the FL and MLA, while maintaining the same spatial resolution. Furthermore, the FOV can be expressed as $\begin{array}{r}{F O V=d_{1}{\times}\frac{f_{\mathrm{F L}}}{f_{\mathrm{M L A}}}{\times}\frac{1}{M}}\end{array}$ ;,when $d_{1}=d_{M L A}$ .Substituting with $d_{MLA}=\frac{D_{cam}}{N},N=R_{xy}\frac{2NA}{\lambda},f_{MLA}=\frac{S_r P f_{FL}}{R_{yy}M}$ and maintaining $\begin{array}{r}{S_{r}=\frac{\lambda}{2N A}\frac{M}{P}}\end{array}$ , we have $FOV=d_{1}\times\frac{f_{\mathrm{FL}}}{f_{\mathrm{MLA}}}\times\frac{1}{M}=\frac{D_{\mathrm{cam}}}{R_{\mathrm{xy}}\frac{2M}{A}}\frac{f_{\mathrm{FL}}}{\frac{\lambda}{2NA}\frac{M}{P}\frac{f_{\mathrm{FL}}P}{R_{\mathrm{xy}}M}}\frac{1}{M}=\frac{D_{\mathrm{cam}}}{M}$ . This suggests atyeof FLFM desig thtdot ompomiee FOVby enineering $S_{r}$ . This condition can be fulfiled in most high-resolution wide-field fuorescence microscopy. Lastly, in our FLFM system, we have noticed that the FOV moderately decreases in a linear fashion, as the sample is moved away from the focal plane.



<div style="text-align: center;"><img src="imgs/img_in_image_box_283_1184_899_1397.jpg" alt="Image" width="50%" /></div>


<div style="text-align: center;">Fig. 12. Analysis of the field of view (FOV) of FLFM. The figure shows the model and symbols to determine the FOV. </div>


## Appendix E: Depth of field (DOF)

In this section, we analyzed the DOF of FLFM (Fig.13). Two factors should be considered when calculating the DOF:

<div style="text-align: center;"><img src="imgs/img_in_image_box_297_264_934_912.jpg" alt="Image" width="52%" /></div>


<div style="text-align: center;">Fig. 13. Analysis of the depth of field (DOF) of FLFM. (a) Ray optics sketch of the model and symbols to determine the DOF based on axial difraction of light. (b) Simulated light propaoo.)optics sketch of the model and symbols to determine the DOF based on the translation of the light-field pattern at varying depths. Scale bars: 20 m. </div>


First, the light-field information on the camera will be out of focus and the intensity will decrease to a threshold value as the emitter is away from the focal plane along the axial direction.Therefore, the DOF can be calculated by the range of detectable intensity considering the diffraction effect in the axial dimension. As shown in Figs. 13(a) and 13(b), the depth can be obtained from the FWHM value of the PSF behind the central microlens on the optical axis along the axial direction. Theoretically, the axial FWHM value of the PSF of the central microlens is $\begin{array}{r}{\frac{N^{2}\lambda}{N A^{2}}+\frac{N^{2}\lambda}{2S_{-}N A^{2}}=32}\end{array}$ m. Numerically, the measurement using our wave-optics model demonstrated the FWHM value of 33 m (Fig. 13(b)), in good agreement with the theoretical result. In this work, because the recontruction relies on deconvolution, which is known to recover the diffracted information outside of the Rayleigh range of the axial PSF, we thereby used the full width of the axial PSF (i.e. 2 times of the FWHM value in the axial dimension) to describe the DOF.Therefore, both our theoretical and numerical models resulted in the DOF of 64 m.

Second, when the object is away from the focal plane, the light-field pattern will spread out or shrink in the lateral dimension. The change of the pattern size is thus limited by the pitch of the MLA (Fig. 13(c)). This value is denoted as $DOF=d_{MLA}\times\frac{f_{FL}}{f_{MLA}}\times\frac{1}{\tan(\theta)}\times\frac{1}{M^2}$ ,where 

$\begin{array}{r}{\tan(\theta)=\frac{d_{\mathrm{M L A}}}{f_{\mathrm{F L}}}}\end{array}$ ·, obtaining a value of 209 m in our experimental system. Beyond this value, the light-field pattern of an emitter is not fully captured by one microlens and thus generates cross talk into the nearby microlenses. Here this value is much greater than the DOF of 64 μm limited by the diffraction.



These two factors set the restriction of the DOF of FLFM, and in this work, we used the minimum value of the two to determine the final DOF (i.e. 64 μm).

## Appendix F: Algorithm flow chart

$$\begin{array}{c}{{\pmb{Z}_{j+1}=\pmb{Z}_{j}+\Delta\pmb{z};}}\\ {{\pmb{Z}_{j}\in[\pmb{Z}_{\operatorname*{m i n}},\pmb{Z}_{\operatorname*{m a x}}].}}\end{array}$$

<div style="text-align: center;">Fig. 14. Algorithm flow chart of FLFM.</div>


## Appendix G: Analysis for reconstruction of the surface-stained structure

In this section, we analyzed the structure of the reconstructed surface-stained microsphere as observed in Fig. 2(c) in the main text. We simulated such a structure $(\mathrm{d i a m e t e r}=20~\mu\mathrm{m})$ and assessed the reconstruction results using diferent axial sampling step sizes (Fig.15). As seen,as tighter sampling slices were taken from Figs. 15(a)-15(c), the reconstructed microsphere appeared a stretched axial pattern and the rugby-like profile was clearly observed in Fig. 15(c),similar to our experimental observation in the top row of Fig. 2(c). The stretch is attributed to the cross talk of each axial slices as they become denser, which project more volumetric information onto limited 2D imaging space on the sensor, the interference of the light field leads to the distortion of the original structure of the object during the deconvolution process.

This problem can be readily resolved by adjusting the FL and the MLA with different parameters to improve the resolution of the system. Here, we numerically reconstruct the continuous microsphere $(\mathrm{d i a m e t e r}=20~\mu\mathrm{m})$ with a different FL (i.e. changed from $f_{\mathrm{F L}}=75$ to 50 mm), in which case the resolution will be improved based on the analysis given above. This 

<div style="text-align: center;"><img src="imgs/img_in_image_box_228_158_1017_619.jpg" alt="Image" width="64%" /></div>


<div style="text-align: center;">Fig. 15. Analysis for the reconstruction of the surface-stained structure $(\mathrm{d i a m e t e r}=20~\mu\mathrm{m})$ (a) top row from left to right, the structure sampled with 5 slices, raw light-field image,reconstructed image of the surface-stained structure, cross-sectional images in x-z of the sampled structure, reconstructed image and the overlay, showing difference between the original and reconstructed sructures due to the limited sampling step size and overlapping spatial information.(b) Same images with respect to (a) but with 11 slices. (c) Top rows are the sameimages with respect to (a) but withinfinite slices (or sufficiently small step size to be exact), showing increasingly continuous structure and the enhanced stretching effect in the axial dimension (e.g. the $\widetilde{3^{\mathrm{rd}}}$ image from the left in the top row of (c))compared to (a)and (b). The bottom row of (c) demonstrates the agreement of the lateral patterns in x-y on the focal plane of the raw (bottom left), reconstructed (bottom middle) and overlay (bottom right) structures. The numerical results are consistent with our experimental observation in Fig. 2(c). Scale bars: 20 m (c, left on the top row), 5 m (c, right on the top row and the bottom row). </div>


improvement mitigated the cross talk of the light field, recovering the original structure after reconstruction (Fig. 16).



<div style="text-align: center;">(a)</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_344_171_959_525.jpg" alt="Image" width="50%" /></div>


<div style="text-align: center;">Fig. 16. Mitigating of the cross talk using a different FL $(f_{FL}=50mm)$ ). Top row from left to right, the densely sampled structure, raw light-field image, and reconstructed image of the surface-stained structure $(\mathrm{diameter}=20\mu\mathrm{m})$ ). Bottom row from left to right, overlay of the original (red) and reconstructed (green)$X-Z$ (left) and $x–y$ (middle) c.otoh the reconstructed hollow structure of the microsphere. Scale bars:$20\mu m$ (top middle), 5 m (bottom middle). </div>


## Appendix H: Notes on the derivation of the equations in Table 1

1.$f_{F L}$ figure, the diameter of the back pupil can be given as $\begin{array}{r}{D_{\mathrm{p u i p l}}=2\times f_{\mathrm{F L}}\times\frac{\mathrm{N A}}{M}}\end{array}$ . As we set $D_{\mathrm{p u i p l}}=D_{\mathrm{c a m}}$ for the maximum use of the camera sensor, the focal length of the FL is finally described as $\begin{array}{r}{f_{\mathrm{F L}}=\frac{D_{\mathrm{c a m}}\times M}{2\mathrm{N A}}}\end{array}$ 



2. As discussed earlier, the lateral resolution $R_{xy}=\frac{\lambda}{2NA_{ML}}\times\frac{f_{FL}}{f_{MLA}}\times\frac{1}{M}$ , and given $\begin{array}{r}{N A_{\mathrm{M L}}=\frac{d_{\mathrm{M L A}}}{2f_{\mathrm{M L A}}}}\end{array}$ the relationship between $R_{x y}$ and $d_{\mathrm{M L A}}$ is presented as $\begin{array}{r}{R_{x y}=\frac{\lambda}{2N A_{\mathrm{M L}}}\times\frac{f_{\mathrm{F L}}}{f_{\mathrm{M L A}}}\times\frac{1}{M}=}\end{array}$ $\begin{array}{r}{\frac{\lambda f_{\mathrm{M L A}}}{d_{\mathrm{M L A}}}\times\frac{f_{\mathrm{F L}}}{f_{\mathrm{M L A}}}\times\frac{1}{M}}\end{array}$ . We define N as the ratio between the FLFM resolution and the resolution of the corresponding wide-field system, namely $\begin{array}{r}{N=R_{x y}/\big(\frac{\lambda}{2N A}\big)}\end{array}$ 

3. Hence,$\begin{array}{r}{N=\frac{\lambda f_{\mathrm{M L A}}}{d_{\mathrm{M L A}}}\times\frac{f_{\mathrm{F L}}}{f_{\mathrm{M L A}}}\times\frac{1}{M}\times\frac{2N A}{\lambda}=\frac{2N A}{M}\times\frac{f_{\mathrm{F L}}}{d_{\mathrm{M L A}}}}\end{array}$ . Given $\begin{array}{r}{D_{\mathrm{c a m}}=\frac{2\mathrm{N A}}{M}\times f_{\mathrm{F L}}}\end{array}$ ,, we obtain $\begin{array}{r}{d_{\mathrm{M L A}}=\frac{D_{\mathrm{c a m}}}{N}}\end{array}$ . Therefore, the occupancy ratio N can also be described as the ratio between the effective pupil size at the $\mathrm{\bf MLA}D_{\mathrm{pupil}}$ and $d_{\mathrm{M L A}}$ 



4.Aswe deitamliaioftdfactio imtofla the physical pixel size, namely $\begin{array}{r}{S_{r}=\frac{\lambda}{2N A_{\mathrm{M L}}}/P}\end{array}$ . We then have $\begin{array}{r}{R_{x y}=\frac{\lambda}{2N A_{\mathrm{M L}}}\times\frac{f_{\mathrm{F L}}}{f_{\mathrm{M L A}}}\times\frac{\stackrel{\frown}{1}}{M}=}\end{array}$ 

$\begin{array}{r}{S_{r}P\times\frac{f_{\mathrm{F L}}}{f_{\mathrm{M L A}}}\times\frac{1}{M},\mathrm{t h u s}f_{\mathrm{M L A}}=\frac{S_{r}P f_{\mathrm{F L}}}{R_{x y}M}}\end{array}$ 



5. The relationship between $d_{1}$ and FOV is given as $\mathrm{FOV}=d_1\times\frac{f_{\mathrm{FL}}}{f_{\mathrm{MLA}}}\times\frac{1}{M},\quad\mathrm{so}\quad d_1=FOV\frac{Mf_{\mathrm{MLA}}}{f_{\mathrm{FL}}}$ 

6.$d_{\max}$ can be directly given from the figure as $\begin{array}{r}{d_{1}\times\frac{D_{\mathrm{c a m}}-d_{\mathrm{M L A}}}{2d_{1}}}\end{array}$ , where [] calculates the greatest integer less than or equal to the variable.



7.$R_{z}$ can be given from Fig.7 in which tan $(\theta^{\prime})$ is replaced by $\frac{d_{\mathrm{m a x}}}{f_{\mathrm{F L}}}$ . Then $\begin{array}{r}{R_{z}=\frac{\lambda}{2N A_{\mathrm{M L}}}\times}\end{array}$ $\frac{f_{\mathrm{FL}}}{f_{\mathrm{MLA}}}\times\frac{1}{\tan(\theta')}\times\frac{1}{M^2}=\frac{\lambda}{2NA_{\mathrm{ML}}}\times\frac{f_{\mathrm{FL}}}{f_{\mathrm{MLA}}}\times\frac{f_{\mathrm{FL}}}{d_{\max}}\times\frac{1}{M^2}=R_{xy}\times\frac{f_{\mathrm{FL}}}{d_{\max}}\times\frac{f_{\mathrm{FL}}}{M}$ . As we have obtained 

$\begin{array}{r}{f_{\mathrm{F L}}=\frac{D_{\mathrm{c a m}}\times M}{2\mathrm{N A}}\;\mathrm{a n d}\;d_{\mathrm{M L A}}=\frac{D_{\mathrm{c a m}}}{N},R_{z}=R_{x y}\times\frac{1}{d_{\mathrm{m a x}}}\times\frac{d_{\mathrm{M L A}}N}{2\mathrm{N A}}=R_{x y}\times\frac{d_{\mathrm{M L A}}}{d_{\mathrm{m a x}}}\times\frac{R_{x y}}{d}=\frac{d_{\mathrm{M L A}}{R_{x y}}^{2}}{4d_{\mathrm{m a x}}}.}\end{array}$ 

8. The DOF is given as twice the axial FWHM value of the PSF, i.e.

$\begin{array}{r}{\mathrm{D O F}=2\Big(\frac{\lambda N^{2}}{N A^{2}}+P\frac{N}{N A}\times\frac{f_{\mathrm{B L}}}{f_{\mathrm{M L A}}}\times\frac{1}{M}\Big).\quad\mathrm{A s}N=R_{x y}\frac{2\mathrm{N A}}{\lambda}\mathrm{a n d}S_{r}=\frac{\lambda}{2N A_{\mathrm{M L}}}/P,D O F=\frac{\lambda}{2N A_{\mathrm{M L}}}/P.}\end{array}$ 

$2(\frac{4{R_{x y}}^{2}}{\lambda}+R_{x y}\frac{f_{M L A}}{f_{F L}}\frac{M}{S_{r}}\times\frac{N}{N A}\times\frac{f_{F L}}{f_{M L A}}\times\frac{1}{M})=2\left(\frac{4{R_{x y}}^{2}}{\lambda}+\frac{R_{x y}}{S_{r}}\times\frac{N}{N A}\right)=2\left(\frac{4{R_{x y}}^{2}}{\lambda}+\frac{R_{x y}}{S_{r}}\times\frac{N}{N A}\right)=$ 

$\begin{array}{r}{2(\frac{4R_{x y}{}^{2}}{\lambda}+\frac{R_{x y}}{S_{r}}\times R_{x y}\frac{2}{\lambda})=\frac{2\left(4+\frac{2}{s_{r}}\right)R_{x y}{}^{2}}{\lambda}}\end{array}$ 



9. The magnification of the FLFM system is given as $\begin{array}{r}{M_{T}=M\times\frac{f_{\mathrm{M L A}}}{f_{\mathrm{F L}}}.\mathrm{S i n c e}f_{\mathrm{M L A}}=\frac{S_{r}P f_{\mathrm{F L}}}{R_{x y}M}}\end{array}$ 

$\begin{array}{r}{M_{T}=M\times\frac{S_{r}P f_{F L}}{R_{x y}M}\times\frac{1}{f_{\mathrm{H L}}}=\frac{S_{r}P}{R_{x y}}.}\end{array}$ 



## Funding 

National Science Foundation (EFMA1830941); National Institute of General Medical Sciences (R35GM124846).



## Acknowledgment 

We acknowledge the support of the NSF-EFMA program and the NIH-NIGMS MIRA program.

## Disclosures 

The authors declare that there are no conflicts of interest related to this article.

## References 

1.G.Lippmann, "Epreuves reversibles,photographies integrales," Comptes Rendus l'Académie des Sci.444, 446–451(1908).
2.M.Levoy,R.Ng,A.Adams,M.Footer,and M.Horowit,"Lihtfildmicroscopy,"ACMTran.Graph.25(3),924–934 (2006).
3.M.evo.aI.owll,"Rcindli litldiouilens arrays,"J.Microsc. 235(2), 144–162 (2009).
4.M.Broxton,L.Grosenick,S.Yang, N.Cohen,A.Andalman,K.Deisseroth,and M.Levoy,"Waveopticstheory and 3-Ddeconvolution forthe light field microscope,"Opt.Express 21(21),25418–25439 (2013).5.R.Prevedel,Y.-G.Yoon,.Hoffmann,N.Pak,G.Wtzstein,S.Kato,T.Scrdel, R.Raskar,M.immer, E.S.Boyden,.i"iuilDiolilopy,"Nat. Methods 11(7), 727–730 (2014).
6.N.C.Pégard, H.-Y.Liu, N. Antipa, M.Gerlock, H. Adesnik, and L. Waller, "Compressive light-field microscopy for 3D neural activity recording,," Optica 3(5), 517–524 (2016).
7. T. Nöbauer, O. Skocek, A.J. Pernía-Andrade, L. Weilguny, F. M. Traub, M. I. Molodtsov, and A. Vaziri, "Video rate volumetric Ca2+ imaging across cortex using seeded iterative demixing (SID) microscopy," Nat. Methods 14(8),811–818 (2017).
8.M.A.Taylor.NbauA.ra-naeF.lummandA.Vai,"Bai-wdeD lldmainof neuronal activity with speckle-enhanced resolution,," Optica 5(4), 345–353 (2018).9.H.Li, C.Guo,D.Kim-Holzapfel, W.Li, Y.Altshuller, B.Schroeder, W.Liu, Y.Meng, J.B.French,K.-I.Takamaru,M.A.Frohman,and S.Jia,"Fast,volumetric live-cell imaging using high-resolution light-field microscopy," Biomed.
Opt. Express 10(1), 29–49 (2019).
10.N. Cohen, S. Yang, A. Andalman, M. Broxton, K. Deisseroth, M. Horowitz, and M. Levoy, "Enhancing the performance of the light field microscope using wavefront coding," Opt. Express 22(1), 727–730 (2014).1.I."of microscopy," in IEEE International Conference on Computational Photography (ICCP) (2017).12.X.Lin,J.WuG.heng,and .a,"Caeraaae litilicopy,"om.O.xpress9),13. A.Lumsdaine and T.Georgiev,The focused plenoptic camera,"in IEEE International Conference on Computational 3179–3189 (2015).
1..Photography (ICCP) (2009).
microscopy with Fourier plane recording," Opt. Express 24(18), 20792–20798 (2016).15.G.SoaJla-a.aao,E.e-OJ..rG,J.Ga-uua,and M. Martinez-Corral, "FIMic: design for ultimate 3D-integral microscopy of in-vivo biological samples," Biomed.
Opt. Express 9(1), 335–346 (2018).


16. L. Cong, Z. Wang, Y. Chai, W. Hang, C. Shang, W. Yang, L. Bai, J.Du, K. Wang, and Q. Wen, "Rapid whole brain imaging of neural activity in freely behaving larval zebrafish (Danio rerio)," eLife 6, e28158 (2017).
17. M. Gu, Advanced Optical Imaging Theory (Springer, 2000).
18.N.DelnandB.Hooker,"ree-spacebeam propagationbetweenarbitrarilyoriented plaesbasedonfull difraction theory: a fast Fourier transform approach,," J. Opt. Soc. Am. A 15(4), 857–867 (1998).
19. F. Dell'Acqua, G. Rizzo, P. Scifo, R.A.Clarke, G. Scotti, and F.Fazio, "A model-based deconvolution approach to solve fiber crossing in diffusion-weighted MR imaging," IEEE Trans. Biomed. Eng. 54(3), 462–472 (2007).
20.A. C. Kak and M. Slaney, "3. Algorithms for Reconstruction with Nondiffracting Sources," in Principles of Computerized Tomographic Imaging (Society for Industrial and Applied Mathematics, 2001), pp. 49–112.
