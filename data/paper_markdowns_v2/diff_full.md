

Optics EXPRESS 

# Towards self-calibrated lens metrology by  differentiable refractive deflectometry 

CONGLi WanG,D Ni CHen,i AND WolFGanG HEidricH*

Visual Computing Center, King Abdullah University of Science and Technology, Thuwal 23955-6900, Saudi Arabia 



®wolfgang.heidrich@kaust.edu.sa 

Abstract: Deflectometry, as a non-contact, fully optical metrology method, is difficult to apply to refractive elements due to multi-surface entanglement and precise pose alignment.Here, we present a computational self-calibration approach to measure parametric lenses using dual-camera refractive deflectometry, achieved by an accurate, differentiable, and efficient ray tracing framework for modeling the metrology setup, based on which damped least squares is utilized to estimate unknown lens shape and pose parameters. We successfully demonstrate both synthetic and experimental results on singlet lens surface curvature and asphere-freeform metrology in a transmissive setting.


©2021 Optical Society of America under the terms of the OSA Open Access Publishing Agreement 

### 1. Introduction 

Refractive lens metrology plays an important role in lens manufacturing, quality control, and reverse engineering. Various techniques have been proposed for general-purpose freeform optical suce lo.Aso-imi o,cmr i  stong interest[1] forits simplicity,low-cost,andinsnsitivity or envronments,from specular surface measurement using computerized phase shifting screens [2–4] to 2D/3D tomography refractive index reconstruction using background oriented Schlieren5–8] and variants 9,10]. However, it is difficult to dirctly apply dectometry toefactivlements,or thellowing asons: (i)Multi-surface interactions mean that deflection shifts are ambiguous and cannot be attributed to a single surface; (i) Lens alignment is sensitive and misalignment may dominate the actual surface deviations rom omial tup;i)asis epresentationis equired oreform surfaces;(iv) Strong refraction leads to large deflections for large-curvature surfaces. There are works demonstratdmultiuracecotruio1,awll artsitrtivetimization [1] and wtlf-alibration[147], psetimation], modl-basdftting[1],dual-amra setu,l,r [23]. However, these techniques are aimed at diferent applications, and cannot fully address all the issues in refractive deflectometry.中Go Gi   wavefront maps), the task is to estimate a set of unknown parameters characterizing the lens surfacesatfttamtaablywllTioblmofaie sgc be generally rephrased as an inverse problem. Thus, an automated, transparent,controllable data analysis process is desired, as a general-purpose computational solution. Compared to the rapid developmentof new instruments, computational techniques remain relatively unexplored,weblievecurrent metrologychiquesould burther imroved by advand computatioal ods.Ose oai-bad altmeof aculir for finding a solution to the problem. However, gradient evaluation is sometimes infeasible usingfi-poxiio c uwumofabAli derivations may notoftntimes be desirablebecauseofthe potetially engthy formulas.Automatiiicaemdumcll,anrooed for solvi roblmsiitli phaseval, n], aseroscopy 

[31], ptychography[32,33],head-mounted displays calibration[34], and transparent object reconstruction[35]. By forward modeling the measurements using an automatic diferentiation engine, a computation graph is constructed, to which the gradients can be evaluated up to numerical precision by repeatedly applying the chain rule [25,36]. Given the gradients, starting from a proper initial guess, unknown model parameters can be iteratively updated. This approach is a general solution to inverse problems, including our problem of interest in this paper.

Direct application of automatic differentiation to our metrology problem is not practical using existing frameworks such as PyTorch [37], because of a few missing blocks: (i) Accuracy.Metrology requires accurate modeling of the measurement setup by ray tracing, from camera to the target lens, and to display screen, with correct shape and pose parameterization. (ii)Differentiability. The ray tracer needs to be diferentiable, such that gradients can be evaluated by back-propagating the acquired data to the unknown lens parameters. (iii) Efficiency. A memoryand computationally efficient pipeline satisfying (i)(ii), for a specially crafted inverse solver to take advantage of.



In this paper, we introduce differentiable refractive deflectometry, a new technique based on automatic differentiation. To mitigate phase ambiguity, we employ a dual-camera refractive deflectometry hardware setup, where screen intersections can be obtained by phase-shifting the display screen (Section 2.1). We build and model the physical metrology setup described by shape and pose parameters, by ray-tracing multiple refractive surfaces using Snell's law.Differentiability is provided using automatic diferentiation, yet to ensure efficiency we propose a differentiable root finder to compute ray-surface intersection (Section 2.2). Utilizing the gradient information, inverse estimation and analysis can be performed, where damped least squares [38]is employed to solve for lens parameters from measurement intersections in a self-calibrated way (Section2.3), and an uncertainty analysis provides a OEcriterion for understanding solution stability (Section 2.4).Both synthetic (Section 3.1) and experimental (Section3.2) results validate our approach.Weblievethe proposed ramework provide anew,general,extensible,and reproducible computational solution to automated data analysis for existing and future deflectometry techniques. Source code and examples will be available at [39].

### 2. Method 

#### 2.1. Problem formulation 

The metrology process involves both hardware image acquisition and software, as in Fig. 1. The setup is based on the phase measuring deflectometry [2], but reconfigured in a refractive mode using a dual-camera setup to introduce view-variant phase measurements for mitigation of surface ambiguity, because both refractive surfaces contribute to the measurable phase. Figure 1(a)shows the schematic diagram. A programmable display screen (Apple MacBook Pro 13.3",pixel pitch 111.8 m) shows a set of 90 phase-shifted sinusoidal patterns, with the target lens placed in front of the screen. Two cameras of F-number f/16 (FLIR GS3-U3-50S5M, pixel pitch 3.45 m) are employed to take grayscale images as in Fig. 1(b). Gamma-correction is applied to ensure a linear relationship between scren andimage pixel values.Grayscaleimages of different phase-shifts $(I_{0^{\circ}},I_{90^{\circ}},I_{180^{\circ}},I_{270^{\circ}})$ are obtained, using 90° phase-shifts. These images encode refractive directional information regarding the testing lens, and hence are processed using the standard four-step phase shifting method followed by phase unwrapping [40], to retrieve observed screen locations $\hat{\mathbf{p}}=(p_{x},p_{y})$ ):

$$p_{x,y}=\mathrm{u n w r a p}\left(\arctan\left(\frac{I_{270^{\circ}}-I_{90^{\circ}}}{I_{0^{\circ}}-I_{180^{\circ}}}\right)\right).$$

Thisl $p_{x}$ and $p_{y}$ , and repeats again separately for both cameras $i=1,2$ , obtaining intersection points $\hat{\mathbf{p}}_{1}$ and $\hat{\mathbf{p}}_{2}$ , as inputs to next step data analysis in Fig. 1(d).



<div style="text-align: center;"><img src="imgs/img_in_image_box_233_142_1003_630.jpg" alt="Image" width="62%" /></div>


<div style="text-align: center;">Fig. 1. Dual-camera refractive deflectometry for lens metrology. (a) Hardware setup.(b) Captured phase-shifted images, from which on-screen intersections $\hat{\mathbf{p}}_{i}$ $(i=1,2)$ are obtained. (c) A ray tracer models the setup by ray tracing each parameterized refractive surface, obtaining the modeled intersections $\mathbf{p}_{i}(\boldsymbol{\theta},\boldsymbol{\phi},\boldsymbol{\mathfrak{t}})$ 1. (d) Unknown θ and pose (, t) are jointly optimized by minimizing the error between $\mathbf{p}_{i}$ and $\hat{\mathbf{p}}_{i}$ . </div>


The target lens is assumed tobe parameterized by , with an unknown pose ,t).Possible θparameterizations are lens curvatures, or freeform coefficients, see Appendix A.for details. A ray tracer models the setup as in Fig. 1(c), resulting in modeled intersections $\mathbf{p}_{i}(\boldsymbol{\theta},\boldsymbol{\phi},\boldsymbol{t})$ . Given pi and $\hat{\mathbf{p}}_{i}$ auml known as the loss function) is minimized, yielding the metrology values $\boldsymbol{\theta}^{*}$ . Here, we minimize the least squared error:

$$\boldsymbol{\theta}^{*},\boldsymbol{\phi}^{*},\boldsymbol{\mathfrak{t}}^{*}=\arg\min_{\boldsymbol{\theta},\boldsymbol{\phi},\boldsymbol{\mathfrak{t}}}\sum_{i=1}^{2}\|\mathbf{p}_{i}(\boldsymbol{\theta},\boldsymbol{\phi},\boldsymbol{\mathfrak{t}})-\hat{\mathbf{p}}_{i}\|_{2}^{2}.$$

We optimize Eq. (2) using damped least squares [38], as will be detailed in Section 2.3. The following elaborates on computation for $\ensuremath{\mathbf{p}}_{i}(\cdot)$ ,the modeling.



#### 2.2. Modeling metrology setup 

Each object (camera, taret lns, scren) is associated with a rigid transformation (R,t) in world coordinate (screen's frame), with a rotation matrix $\mathbf{R}\in\mathbb{R}^{3\times\vec{3}}$ and a translation vector $\pmb{t}\in\mathbb{R}^{3}$ ！Ray tracin is performed in local rames. For posetimation,thetarget ens transformation $(\mathbf{R}(\pmb{\phi}),\pmb{\mathfrak{t}})$ can be determined from the six degre-of-freedom parameters (, t) where $\pmb{\phi}\in\mathbb{R}^{3}$ are the rotation angles around $(x,y,z)$ axes. Cameras are treated as perspective pinholes, with the intrinsic and extrinsic parameters obtained from calibration [41].



Rays are generated for each image pixel by the following procedure:

### 1. Sampling from camera pinhole model;

2.Intersecting surfacesof thetarget ens via a rootfinder, refractionand deection by Snell's law, and hence the outgoing rays are associated with lens parameters θ and pose $(\mathbf{R}({\pmb\phi}),{\pmb t});$ 

3. Reachingtoards a pesumably planar dislay ren,obtaining the modled intersections $\mathbf{p}_{i}(\boldsymbol{\theta},\boldsymbol{\phi},\mathfrak{t})$ for both cameras.



Ofthee oent for aspheres and freeform surfaces, which do not have closed-form analytical solutions. The intersection problem requires solving for intersection $(x,y,z)$ and a ray marching distance t for optical surface $f(x,y,z;\boldsymbol{\theta})=0$ , given a ray $(\mathbf{o},\mathbf{d})$ oforigin $\mathbf{o}=(o_{x},o_{y},o_{z})$ and direction $\mathbf{d}=(d_{x},d_{y},d_{z})$ of unit length. Mathematically:

$$\mathrm{find}\quad t>0\quad\mathrm{substack}\mathrm{subject to}\quad f(x,y,z;\boldsymbol{\theta})=f(\mathbf{o}+t\mathbf{d};\boldsymbol{\theta})=0.$$

Eq. (3) can be solved using an iterative root finder, with the iterations directly unrolled for gradients, so that ray marching distances t can be related through lens parameters $\pmb{\theta}$ via automatic differentiation. However, this straightforward approach is not efficient and is memory consuming because of storing the intermediate iteration variables and their derivatives for every ray in the image. Fortunately, there is an analytic approach for the desired gradient to be computed outside of automatic differentiation. Denote the solution to Eq. (3) as $t^{*}$ , and exploit the implicit function theorem for differentiation w.r.t. θ:

$$f(\mathbf{o}+t^{*}(\boldsymbol{\theta})\mathbf{d};\boldsymbol{\theta})=0\qquad\mathrm{a n d}\qquad\big(\nabla f\cdot\mathbf{d}\big)\frac{\partial t^{*}}{\partial\boldsymbol{\theta}}+\frac{\partial f}{\partial\boldsymbol{\theta}}=0.$$

Rearranging above, yields an analytic formula for gradient:

$$\frac{\partial t^{*}}{\partial\boldsymbol{\theta}}=-\frac{1}{\nabla f\cdot\mathbf{d}}\frac{\partial f}{\partial\boldsymbol{\theta}}.$$

In other words, we can first compute $t^{*}$ without automati direntiation and n intermediate variables stored), and then amend its gradient back to automatic differentiation by Eq. (5). We employ Newton's method for obtaining $t^{*}$ ,initializedn-iular timate $t^{(0)}=(\widehat{z_{f}-o_{z}})/d_{z}$ with iteration stops when the residual is smaller than tolerance. The method converges in a few iterations. When properly setup, with no target lens present, the modeled image matches the real image reasonably well as in Fig. 2, demonstrating the physical realism of the ray tracer. Blurry edges are from diffraction, which is ignored in this paper, since we describe a ray optics approach.

<div style="text-align: center;"><img src="imgs/img_in_image_box_258_986_941_1195.jpg" alt="Image" width="55%" /></div>


<div style="text-align: center;">Fig.2. Assuming pinhole camera model and planar screen, our ray tracer reproduces captured images in high fidelity. </div>


#### 2.3. Optimization using damped least squares 

In this sub-section, we slightly abuse the notation by letting $\boldsymbol{\theta}:=(\boldsymbol{\theta},\boldsymbol{\phi},\boldsymbol{t})$ .Our target is to estimate $\boldsymbol{\theta}\in\mathbb{R}^{n}$ in Eq. (2) for the following using damped least squares [38]:

$$\boldsymbol{\theta}^{*}=\arg\operatorname*{m i n}_{\boldsymbol{\theta}}~\sum_{i=1}^{2}\|\mathbf{p}_{i}(\boldsymbol{\theta})-\hat{\mathbf{p}}_{i}\|_{2}^{2},$$

where recall that function $\mathbf{p}_{i}(\cdot)\colon\mathbb{R}^{n}\mapsto\mathbb{R}^{m}$ maps from the n unknown parameters to the m modeled intersection points, and $m\gg n$ . To obtain an iterative solution to Eq. (6), at current estimate $\boldsymbol{\theta}^{(k)}$ , we solve for a small change of $\Delta\boldsymbol{\theta}$ to obtain $\boldsymbol{\theta}^{(k+1)}$ ', such that:

$$\boldsymbol{\theta}^{(k+1)}=\boldsymbol{\theta}^{(k)}+\Delta\boldsymbol{\theta},\qquad\mathrm{w h e r e}\quad\Delta\boldsymbol{\theta}=\arg\operatorname*{m i n}_{\Delta\boldsymbol{\theta}}\sum_{i=1}^{2}\|\mathbf{p}_{i}(\boldsymbol{\theta}^{(k+1)})-\hat{\mathbf{p}}_{i}\|_{2}^{2}.$$

The iteration stops when a stopping criterion is met. At each step , each non-linear function $\mathbf{p}_{i}(\cdot)$ is approximated using a first-order Taylor expansion:

$$\mathbf{p}_{i}(\boldsymbol{\theta}^{(k+1)})=\mathbf{p}_{i}(\boldsymbol{\theta}^{(k)}+\Delta\boldsymbol{\theta})\approx\mathbf{p}_{i}(\boldsymbol{\theta}^{(k)})+\mathbf{J}_{i}\Delta\boldsymbol{\theta},\qquad\mathrm{w h e r e\;J a c o b i a n}\quad\mathbf{J}_{i}=\frac{\partial\mathbf{p}_{i}}{\partial\boldsymbol{\theta}}\in\mathbb{R}^{m\times n}.$$

With Eq. (8), the least squares problem in Eq. (7) can be solved using the damped normal equation to ensure robustness, by adding a diagonal matrix $\mathbf{D}\in\mathbb{R}^{n\times n}$ scaled by an iteratively changing damping factor.$\rho{>}0$ :

$$\left(\sum_{i=1}^{2}\mathbf{J}_{i}^{T}\mathbf{J}_{i}+\rho\mathbf{D}\right)\Delta\boldsymbol{\theta}=\sum_{i=1}^{2}\mathbf{J}_{i}^{T}\left(\hat{\mathbf{p}}_{i}-\mathbf{p}_{i}(\boldsymbol{\theta}^{(k)})\right).$$

In practice, we found D being an identity matrix yields satisfactory results.

Features of automatic diferentiation can be employed to efficiently solve the linear system in Eq. (9). Notice that the Jacobian $\mathbf{J}_{i}$ is a tall matrix $(\operatorname{s i n c e}m\gg n)$ 1, and it can be efficiently evaluated in a column-wise fashion using the forward-mode, hence obtaining $\mathbf{J}_{i}^{T}\mathbf{J}_{i}$ on the left-hand-side,whereas the right-hand-side can be obtained by reverse-mode without explicitly constructing $\mathbf{J}_{i}^{T}$ . These speed improvements in terms of efficiency would not be possible without automatic differentiation.



Our framewokand te r eimm $\mathbf{P y}$ Th,o framework provides a straightforward way to accurately evaluate gradients. For a small set of $\boldsymbol{\theta}\in\mathbb{R}^n$ when $n{<}20$ , the solver converges in a few seconds on a modern GPU, indicating practical usage of the method for fast metrology applications. Further speed improvements are possible using optimized high-performance code or on advanced computing platforms.

#### 2.4. Uncertainty variance analysis 

We can perform an uncertainty analysis on Eq. (6) to understand solution stability. Analyzing the derivatives (ignoring constants):

$$\begin{array}{r}{\partial\mathrm{l o s s}=\sum_{i=1}^{2}(\mathbf{p}_{i}(\boldsymbol{\theta})-\hat{\mathbf{p}}_{i})\cdot\mathbf{J}_{i}\partial\boldsymbol{\theta}=\mathbf{v}\cdot\partial\boldsymbol{\theta},\qquad\mathrm{w h e r e}\quad\mathbf{v}=\sum_{i=1}^{2}\mathbf{J}_{i}^{T}(\mathbf{p}_{i}(\boldsymbol{\theta})-\hat{\mathbf{p}}_{i}).}\end{array}$$

With an independence assumption on $\boldsymbol{\theta}\in\mathbb{R}^{n}$ (when properly parameterized) and equal prior probabilities, denoting diag(·) as a diagonal matrix formed by the corresponding vector, the uncertainty variance of each element of variable θ, is hence calculated as:

$$\sigma_{\mathrm{l o s s}}^{2}=\mathbf{v}^{T}\mathrm{d i a g}(\sigma_{\boldsymbol{\theta}}^{2})\mathbf{v}\qquad\Rightarrow\qquad\sigma_{\boldsymbol{\theta}}^{2}=\frac{\sigma_{\mathrm{l o s s}}^{2}}{n|\mathbf{v}|^{2}},$$

where $\sigma_{loss}^{2}$ can be calculated from the optimal point, and $|\mathbf{v}|^{2}$ is the element-wise squared of the vector v.



### 3. Results 

#### 3.1. Synthetic results 

Verification experiments are performed in simulation to verify the proposed self-calibration method. Figure 3 simulates a convex-concave lens (Thorlabs LE1234) under metrology test for curvature estimation, where the desired parameters $\boldsymbol{\theta}=(c_{1},c_{2})$ are the two surface curvatures $c_{1}$ and $c_{2}$ .The lens sufered from a minor misalignment perturbation $\pmb{\phi}=(-0.3^{\circ},0.5^{\circ},0^{\circ})$ and $\mathbf{t}=$ $\mathbf{t}_{0}+\Delta\mathbf{t}$ :where $\pmb{\mathrm{t}}_{0}$ is obtained from triangulation but t is deviated by $\Delta\mathbf{t}=(0.5mm,0.5mm,0.5mm)$ ).Synthetic images were corrupted by Gaussian noise. When assuming perfect alignment $(\boldsymbol{\phi}=\boldsymbol{0}$ ,$\Delta\mathbf{t}=\mathbf{0},\mathbf{i}.\mathbf{e}$ ., only optimizing θ), the solver cannot be employed to predict the correct curvatures because of misalignment systematic errors in the measurement, whereas a self-calibration estimation (, t, θ) is successful in error reduction, and a more accurate curvature estimate as in the table. This is illustrated in the final errors of the two methods, that the self-calibration approach (optimizing θ, , t) produces a final error of more than a magnitude smaller compared to the non self-calibrated approach optimizing θ only. This demonstrates the superiority of joint shape and pose parameter estimation, which would not be viable without our accurate modeling of the setup.



<div style="text-align: center;"><img src="imgs/img_in_image_box_242_603_984_1065.jpg" alt="Image" width="60%" /></div>


<div style="text-align: center;">Fig. 3. Lens curvature $\boldsymbol{\theta}=(c_{1},c_{2})$ metrology using synthetic data. Intersection error maps $\|\mathbf{p}_{i}-\hat{\mathbf{p}}_{i}\|$ are shown. Metrology data analysis is sensitive to minor misalignment, and a self-calibration approach is preferable by jointly optimizing , , t.</div>


Similar conclusion also holds for freeform metrology, as in Fig.4 where an asphere-freeform lens is simulated, suffered from the same misalignment (, t), where the task is to estimate the cubic B-spline freeform surface coefficients , knowing the asphere profile. This one-surface constrtil over-fit $\hat{\mathbf{p}}_{i}$ ,wee affects metrologyresults.I contrasta oint optimizationof bothθand ,t) sigificantly reduces the error, showing the benefit of a self-calibration approach.

#### 3.2. Experimental results 

Experimental results are supportive. Figure 5 shows experimental results on lens curvature metrology for a convex-concave lens (Thorlabs LE1234). The lens was amounted and placed  <div style="text-align: center;"><img src="imgs/img_in_image_box_244_138_1007_716.jpg" alt="Image" width="62%" /></div>


<div style="text-align: center;">Fig. 4. Freeform lens metrology using synthetic data. Intersection error maps $|\mathbf{p}_{i}-\hat{\mathbf{p}}_{i}|$ and freeform surface error are shown. A self-calibration approach produces better results.</div>


in front of the screen at a distance of approximately 5 cm. The target lens pose $(\pmb{\phi},\pmb{\mathrm{t}}_{0}+\Delta\pmb{\mathrm{t}})$ is assumed to be in perfect angular alignment $\pmb{\phi}=\pmb{0}$ , but suffered from minor displacement errors $(\Delta\mathbf{t}\neq\mathbf{0})$ ,with the nomial oigin $\mathbf{t}_{0}$ c from planar surfaces $(c_{1}=c_{2}=\infty)$ , our optimized curvatures are close to the manufacturer design parameters (Table 1), though the fitting error incrases slightly at lens boundary. Two tr $\phi$ and ∆t optimized. Surface curvatures metrology results are shown in Table 1, our metrology results were close to the 

<div style="text-align: center;"><img src="imgs/img_in_image_box_277_1060_985_1439.jpg" alt="Image" width="57%" /></div>


<div style="text-align: center;">Fig. 5. Experimental lens curvature metrology for LE1234.</div>


nominal manufacturer's specifications, demonstrating the feasibility of our method to measure multi-surface curvatures.



<div style="text-align: center;">Table 1. Experimental singlet lens curvature metrology results.</div>



<div style="text-align: center;"><html><body><table border="1"><thead><tr><td>(33.65, 100.00) (34.68, 101.41)</td><td>(−82.23, −32.14) (−82.41, −32.61)</td><td>(64.38, ∞) (62.10, 828.39)</td><td></td><td>truth</td></tr></thead><tbody><tr><td>−100</td><td>100</td><td>125</td><td></td><td>smo focal length</td></tr><tr><td>LF1822</td><td>LE1234 Table 1. Experimental singlet lens curvature metrology results.</td><td>LA1986</td><td>[mm] / lens name</td><td></td></tr></tbody></table></body></html></div>


Freeform lens experimental metrology results are also encouraging. The target optics is an asphere-freeform lens, whose two surfaces were discretely sampled and measured by a coordiate measuring machine (CMM) machine as ground truth. This freeform lens was mounted and placed 

<div style="text-align: center;"><img src="imgs/img_in_image_box_292_494_953_882.jpg" alt="Image" width="54%" /></div>


<div style="text-align: center;">(a) Raw images and intersection error maps </div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_324_940_914_1317.jpg" alt="Image" width="48%" /></div>


<div style="text-align: center;">(b) Reconstruction surfaces </div>


<div style="text-align: center;">Fig. 6. Experimental asphere-freeform lens metrology. (a) Raw images with the regions of interest (contoured by red lines) and optimization intersection errors. (b) Reconstruction comparison against CMM metrology results as ground truth. </div>


approximately 5 cm in front of the screen for measurement (see Fig. 1(b)). As in simulation, we assume that an approximate surface profile of the asphere is given, and would like to solve for the freeform surface, with the pose unknown. Results are shown in Fig.6. Our solver optimizes the metrology data to a small residual intersection errors for both cameras, as in Fig. 6(a). Though wrongly initialized for the asphere surface, the solver optimizes back to the correct orientation,and the reconstruction surfaces are visually similar to the ground truth in Fig. 6(b), but are spatially transformed due to different alignment in deflectometry experiment and CMM data metrology, and double-surface entanglement as well in that the solution space is too huge to over-fit the data. Yet, our method provides an initial method to qualitatively profile both surfaces,when there is limited prior knowledge available. We have demonstrated the capability of the proposed method for surface metrology, especially for surface curvature estimations.

### 4. Discussion and Conclusion 

Given current results, several avenues for future improvements are apparent. The underlining principle of this paper shares a high similarity with methods in profilometry, from which common issues such as influence of phase coding and variation of light transmittance can be analyzed and resolved [42]. On the hardware side, current image acquisition pipeline could be extended to a multi-angle tomography setup, or encode/decode intersections instantaneously to improve acquisition speed [43]. Doublets are also possible by incorporating ours into a data fusion pipeline].In software,hanks toautomatic frntiation,ataiable gradintinformatio allows for aamilyof lrsto bemod or aclrated nvernce,mpmising dferent trade-off factors. We may also extend ray-surface interaction beyond pure refraction and take optical aberrations intoconsideration5,4]. Suitable parametriationialso impora full characterization of optical elements. Lastly, uncertainty analysis deserves more attention,as deflectometry itself requires a computationally heavy procedure which may introduce data misinterpretation.



In conclusion, we have demonstrated differentiable refractive deflectometry for self-calibrated lens metrology. Given the phase-shifting images, a fringe analysis provides measurement intersection points for the method to proceed, where both the unknown lens parameters and the pose are jointly optimized using a differentiable ray tracer. We believe the opened up new computational possibilities for lens metrology data analysis andotherrlevant application aras.

### A. Lens parameterization 

#### A.1.Surface parameterization 

We parameterize each lens surface in the implicit form:

$$f(x,y,z;\boldsymbol{\theta})=0.$$

We consider three specific types of parameterized lens surfaces to represent lens and freeform surfaces, yet in theory alternative parameterization forms (see [47]) should also work. Surfaces are defined in a Cartesian coordinate system $(x,y,z)$ 1, with z-axis being chosen as the optical axis (if any).



##### A.1.1. Aspheres 

Let $\rho=x^{2}+y^{2}$ sinceasphrllcTeaceunction $s(\rho)$ aspheric surfaces and its derivative with respect to ρ are:

$$s(\rho)=\frac{c\rho}{1+\sqrt{1-\alpha\rho}}+\sum_{i=2}^{n}a_{2i}\rho^{i},$$

$$s^{\prime}(\rho)=c\frac{1+\sqrt{1-\alpha\rho}-\alpha\rho/2}{\sqrt{1-\alpha\rho}\left(1+\sqrt{1-\alpha\rho}\right)^{2}}+\sum_{i=2}^{n}a_{2i}i\rho^{i-1},$$

where c is the curvature,$\alpha=(1+\kappa)c^{2}$ with κ being the conic coeffi cient, and $a_{2i}\mathrm{s}$ sare higherorder coefficients. Spherical surfaces are special cases of aspheric surfaces, with $\kappa=0$ and $a_{2i}=0(i=2,\ldots,n)$ .In implicit form:

$$f(x,y,z;\boldsymbol{\theta})=s(\rho)-z,$$

$$\nabla f(x,y,z;\boldsymbol{\theta})=(2s^{\prime}(\rho)x,2s^{\prime}(\rho)y,-1),$$

where differentiable parameters $\boldsymbol{\theta}=(c,\kappa,a_{2i})$ 

##### A.1.2. XY polynomials 

XY polynomial surfaces extend lens surface representation beyond axial symmetry. The implicit surface function $f(x,y,z;\boldsymbol{\theta})$ and its spatial derivatives are:

$$f(x,y,z;\boldsymbol{\theta})=\sum_{j=0}^{J}\sum_{i=0}^{j}a_{i,j}x^{i}y^{j-i}+b z^{2}-z,$$

$$\nabla f(x,y,z;\boldsymbol{\theta})=\left(\sum_{j=1}^{J}\sum_{i=0}^{j}a_{i,j}i x^{i-1}y^{j-i},\sum_{j=1}^{J}\sum_{i=0}^{j}a_{i,j}(j-i)x^{i}y^{j-i-1},2b z-1\right),$$

where differentiable parameters $\boldsymbol{\theta}=(b,a_{i,j})$ 

##### A.1.3. B-splines 

We employ B-splines [48] to represent high degree-of-freedom freeform surfaces. In general, the sag distance function $g(x,y)$ is represented as a spline of degree (in our case, it is three, ie. the cubic B-spline) on the rectangle area, with predefined number of knots and knot positions. With that, spline functions $S_{i,j}(x,y)$ are fixed, and $g(x,y)$ is determined by spline coefficients $c_{i,j};$ 

$$f(x,y,z;\boldsymbol{\theta})=\sum_{i}^{n}\sum_{j}^{m}c_{i,j}S_{i,j}(x,y)-z,$$

$$\nabla f(x,y,z;\boldsymbol{\theta})=\left(\sum_{i}^{n}\sum_{j}^{m}c_{i,j}\nabla_{x}S_{i,j}(x,y),\sum_{i}^{n}\sum_{j}^{m}c_{i,j}\nabla_{y}S_{i,j}(x,y),-1\right),$$

where differentiable parameters $\boldsymbol{\theta}=(c_{i,j})$ ,and the spatial gradients of the spline functions $\nabla_{x}S_{i,j}$ and $\nabla_{x}S_{i,j}$ are efficiently evaluated via modified de-Boor's algorithm [48].

#### A.2. Lens type 

In simulation and experiments, two types of lenses were considered:

• Singlet spherical lens, where the two surface curvatures are of interest, and $\boldsymbol{\theta}=(c_{1},c_{2})$ 

• Asphere-freeform lens, where one surface is asphere (parameterized by XY polynomial coefficients $\mathbf{\theta}_{\mathrm{X Y}})$ ), while another is cubic B-spline freeform surface (parameterized by $\boldsymbol{\theta}_{\mathrm{spline}})$ . In simulation $\boldsymbol{\theta}=\boldsymbol{\theta}_{\mathrm{s p l i n e}}$ :and in experiment $\boldsymbol{\theta}=(\boldsymbol{\theta}_{\mathrm{X Y}},\boldsymbol{\theta}_{\mathrm{s p l i n e}})$ 1.

We also assumed the following parameters are known: (i) lens diameter (ii) center thickness (iii)material refractive index at 562 nm. Although these additional parameters could also be jointly optimized using the proposed framework.



Funding).



freeform lens and its surface data.



Disclosures. The authors declare no conflicts of interest.

Datv.

## References 

1.C. Faber, E. Olesch, R.Krobot, and G.Häusler, "Defectometry challenges interferometry: The competition gets tougher!" in Interferometry XVI: Techniques and Analysis, vol. 8493 (International Society for Optics and Photonics,2012), p. 84930R.
2. M.C. Knauer, J. Kaminski, and G. Hausler, "Phase measuring deflectometry: A new approach to measure specular free-form surfaces,"in Optical Metrology in Production Engineering, vol. 5457 (International Society for Optics and Photonics, 2004), pp. 366–376.
3.P. Su, R.E.Parks, L. Wang, R.P.Angel, and J.H.Burge, "Softwareconfigurable optical test system: Acomputerized reverse hartmann test," Appl.Opt. 49(23), 4404–4412 (2010).
4.F.Willomitzer, C.-K.Yeh, V.Gupta, W. Spies,F.Schiffers, A.Katsaggelos, M.Walton,and O.Cossairt, "Hand-guided qualitativedeflectometry withamobiledevice,"Opt.Express28(7),9027–9038(020.5.H. Richard and M. Raffel, "Principle and applications of the background oriented schlieren (BOS) method," Meas.
Sci. Technol. 12(9), 1576–1585 (2001).
6.B.Atcheson,I.Ihrke, W.Heidrich,A.Tevs, D.Bradley, M.Magnor, and H.-P. Seidel, "Time-resolved 3D capture of non-stationary gas flows," ACM Trans. Graph. 27(5), 1–9 (2008).
7.I. Ihrke, K.N.Kutulakos, H. P.Lensch, M.Magnor, and W. Heidrich, "Transparent and specular object reconstruction,"in Computer Graphics Forum, vol. 29 (Wiley Online Library, 2010), pp. 240–2426.8.C.Wang,Q.Fu,X.Dun,and W.Heidrich,"Quantitative phaseandintenity microscopyuingsnapshot white light wavefront sensing," Sci. Rep. 9(1), 13795 (2019).
9.G.Wetstin,R.Rakar,and W.Heidrich,"Hand-hldlirphotograph wlihtfld probes"inIEEE International Conference on Computational Photography, (IEEE, 2011), pp. 1–8.10.C.Wag, X.u.Fu,dW.Hd,"Uhuidetr".x2(2),
13736–13746 (2017).
11.D.Wang, P.Xu, Z.Wu, X.Fu,R. Wu,M.Kong,J.Liang, B.Zhang,and R.Liang, "Simultaneous multisurface measuomd",12.J.Ye,.NiX.hang,W.Wang,and .Xu,"imulaous aumetof doubleuraeofaaret lenses with phase measuring deflectometry,." Opt. Lasers Eng. 137, 106356 (2021).
13..R.G.,W.a...uT.a.W.mMryetics measurement using an iterative reconstructiontechnique,,"Opt.Lett.43(9),2110–2113 (2018).14.E.e.andGH"Dlii".Gao,
(2011), p. P27.
15. H. Ren,F.Gao,and X.Jiang,"Iterativeoptimizationcalibration method for stereo deflectometry,"Opt.Express 23(17), 22060–22068 (2015).
16.Y.Xu,F.Gao,.hang,andXJiang,"Aholisticalibratiomthod wititativeditortiocompensationfor stereo deflectometry," Opt. Lasers Eng. 106, 111–118 (2018).
17.X. Xu, X. Zhang, Z.Niu, W. Wang, Y. Zhu, and M. Xu, "Self-calibration of in situ monoscopic deflectometric measurement in precisionopticalanufacturing,"Opt.Express27(5),72–536(219).18. C. Sun, Y.Zheng, F.Zeng, Q. Xue, W.Dai, W.Zhao,and L.Huang, "Simultaneous measurement of displacement,pitch, and yaw angles of a cavity output mirror based on phase measuring deflectometry," Appl. Opt. 59(10),19.L.Huag,J.u.Gao,.McProJ.a,d .Idr,"Moal paugmry"Ot.3270–3284 (2020).
2....i Express 24(21), 24649–24664 (2016).
deflectometry based on phase difference minimization," Opt.Express 28(21),31658–31674 (2020).21.YC.un.Duoclcbic reconstruction," Appl. Opt. 59(28), 8526–8539 (2020).
22.L.Huang,H.Cho,W.haoL.R.Grave,andD.WKim"Aativerromriculltngown freeform optics metrology," Opt. Lett. 41(23), 5539–5542 (2016).
2..C.G""2..".Proc. DGao, (2008), p. A24.
25.A.S.Julngand J.R.eup,"Aplictionsofaloitmcititiotoaerivalalortms"J.pt.oc.29(11), 17125–17139 (2021).
Am.A 31(7), 1348–1359 (2014).


26.optical systems," Schedae Informaticae 21, 169–175 (2012).
27.J.-B.la-dGooflanba differentiation of computational graphs,"J.Opt. Soc. Am. A 34(7), 1146–1151 (2017).28.G.té-F.mp"s 27(20), 28279–28292 (2019).
29.G.Côt, J.-F.Lalondeand S.Thibault,"Dep learning-enabledframework for automatic lens design starting point generation,," Opt. Express 29(3), 3841–3854 (2021).
30.C. Wang, N.Chen, and W.Heidrich,"Lens design optimization by back-propagation,"in International Optical Design Conference, (Optical Society of America, 2021), pp. JTh4A–2.
31. E.Bostan, R. Heckel, M. Chen, M. Kellman, and L. Waller, "Deep phase decoder: Self-calibrating phase microscopy with an untrained deep neural network," Optica 7(6), 559–562 (2020).
32. S.Ghosh, Y. S. Nashed, O.Cossairt and A.Katsaggelos,"ADP: Automatic differentiation ptychography," in IEEE International Conference on Computational Photography, (IEEE, 2018), pp. 1–10.33. S.Kandel,S.Maddali,M.Allain, S.O.Hruszkewycz,C.Jacobsen,and Y.S.Nashed,"Using automatic diferentiation as a general framework for ptychographic reconstruction,"Opt.Express 27(13),18653–18672 (2019).34. Q.Guo, H. Tang, A.Schmitz, W. Zhang,Y.Lou, A.Fix,S.Lovegrove, and H.M.Strasdat, "Raycast calibration for augmented reality HMDs with off-axis reflective combiners," in IEEE International Conference on Computational Photography, (IEEE, 2020), pp. 1–12.
35.J.Lyu,B.Wu,D.LichinskiD.Cohen-O,andH.Huang,"Difrentiablereaction-tracing or mehrconstruction of transparent objects,," ACM Trans. Graph. 39(6), 1–13 (2020).
36.A.G.Baydin,B.A.Pearlmutter, A.A.Radul,and J.M. Siskind,"Automatic differentiation in machine learning: A survey," Journal of Machine Learning Research 18(153), 1–43 (2018).
37.A. Paszke, S.Gross, F. Massa, A. Lerer, J. Bradbury, G. Chanan, T. Killeen, Z. Lin, N. Gimelshein, L. Antiga,A. Desmaison, A. Kopf, E. Yang, Z. DeVito, M. Raison, A. Tejani, S. Chilamkurthy, B. Steiner, L. Fang, J. Bai,and S. Chintala, "PyTorch: An imperative style,high-performance deep learning library," in Advances in Neural Information Processing Systems, H.Wallach,H.Larochelle, A.Beygelzimer, F.d'Alché-Buc, E.Fox, and R.Garnett,eds. (Curran Associates, Inc., 2019), pp. 8024–8035.
38.J. Meiron, "Damped least-squares method for automatic lens design," J. Opt. Soc. Am. 55(9), 1105–1109 (1965).39. https://github.com/vccimaging/Dif Deflectometry (2021).
40. M.A. Herraez, D.R. Burton, M. J.Lalor, and M.A.Gdeisat, "Fast two-dimensional phase-unwrapping algorithm based on sorting by reliability following a noncontinuous path," Appl.Opt.41(35), 7437–7444 (2002).41.Z. Zhang, "A flexible new technique for camera calibration," IEEE Trans. Pattern Anal. Machine Intell. 22(11),1330–1334 (2000).
42.C.uo,S.Feng,L.Huang,T.Tao,W.Yin,and .Chen,"Phasehitingalgorithmsorrnge projectionprofilometry:Areview," Opt. Lasers Eng. 109, 23–59 (2018).
43.I.Trumpr.ho,nd.W.im,"Iaaousaeiigcmy"Op.xpr9–07(2016).
44. A.Mik and P.Pokorny, "Simple method for determination of parameters of cemented doublet," Appl.Opt.55(20),5456–5458 (2016).
45.S.K.PatraJ.BartchM.Kalms,and R.B.Bergmann,"Phasemeasurement deviation in deflectometry due to propertiesoftechnical surfaces,"in Applied Optical MetrologyIIl,vol.11102(International SocietyforOpticsand Photonics, 2019), p. 111020Q.
46.X.ha,.iJ.Yd.Xu,"ioiindsinmtry,"Opt. Lett. 46(9), 2047–2050 (2021).
47.J.Ye, L.Chen, X.Li,Q.Yuan,and Z.Gao, "Review of optical freeform surface representationtechnique and its application,," Opt. Eng. 56(11), 110901 (2017).
48.C.De Boor, A practical guide to splines: Revised edition (Springer-Verlag, 2001), vol.27, pp.109–115.