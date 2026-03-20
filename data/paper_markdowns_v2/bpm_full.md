

# Optical tomographic image reconstruction based on  beam propagation and sparse regularization 

Ulugbek S.Kamilov,Membr,EEE,IoaiN.Papadooulos,Moreza H.horh,AlexandreGoy, Cedric Vonesch, Michael Unser, Fellow, IEEE, and Demetri Psaltis, Fellow, IEEE 

Abstract—Optical tomographic imaging requires an accurate forward model as well as regularization to mitigate missingdata artifacts and to suppress noise. Nonlinear forward models can provide more accurate interpretation of the measured data than their linear counterparts, but they generally result in computationally prohibitive reconstruction algorithms. Although sparsity-driven regularizers significantly improve the quality of reconstructed image, they further increase the computational burden of imaging. In this paper, we present a novel iterative imaging method for optical tomography that combines a nonlinear forward model based on the beam propagation method (BPM) with an edge-preserving three-dimensional (3D) total variation (TV) regularizer. The central element of our approach is a time-reversal scheme, which allows for an efficient computation of the derivative of the transmitted wave-field with respect to the distribution of the refractive index. This time-reversal scheme together with our stochastic proximal-gradient algorithm makes it possible to optimize under a nonlinear forward model in a computationally tractable way, thus enabling a high-quality imaging of the refractive index throughout the object. We demonstrate the effectiveness of our method through several experiments on simulated and experimentally measured data.Index Terms—optical phase tomography, total variation regularization, compressive sensing, sparse reconstruction, beam propagation method, stochastic proximal-gradient 

### I. INTRODUCTION 

Optical tomography is a popular and widely investigated technique for three-dimensional (3D) quantitative imaging of biological samples. In a typical setup, the sample is illuminated with a laser over multiple angles and the scattered light is holographically recorded giving access to both the amplitude and the phase of the light-field at the camera plane. The refractive index distribution of the sample is then numerically reconstructed from the scattered light-field by relying on a model describing the interaction between the sample and the light. Quantitative reconstruction of the refractive index is a central problem in biomedical imaging as it enables the 

This work was supported by the European Research Council under the European Union's Seventh Framework Programme (FP7/2007-2013)/ERC Grant Agreement 267439.



U. S.Kamilov (email:kamilov@merl.com)is with Mitsubishi Electric Research Laboratories, Cambridge, MA,USA. This work was completed while he was with the Biomedical Imaging Group, École polytechnique fédérale de Lausanne.



I. N. Papadopoulos (email: ioannis.papadopoulos@epfl.ch), M. H.Shoreh (email: morteza.hasanishoreh@epffl.ch),A. Goy (email: alexandre.goy@epfl.ch),and D.Psaltis(email: demetri.psaltis@epfl.ch)are with the Optics Laboratory, École polytechnique fédérale de Lausanne.

C. Vonesch (email: cedric.vonesch@epfl.ch) and M. Unser (email:michael.unser@epfl.ch) are with the Biomedical Imaging Group, École polytechnique fédérale de Lausanne.



visualization of the internal structure, as well as physical properties, of nearly transparent objects such as cells.

Most approaches for estimating the refractive index rely on various approximations to linearize the relationship between the refractive index and the measured light-field. For example,one approach is based on the straight-ray approximation and interprets the phase of the transmitted light-field as a line integral of the refractive index along the propagation direction.The reconstruction under straight-ray approximation can be performed efficiently by using the filtered back-projection (FBP) algorithm [1]. Another popular approach is diffraction tomography that was proposed by Wolf [2] and later refined by Devaney [3]. Diffraction tomography establishes a Fourier transform-based relationship between the measured field and the refractive index, which enables the recovery of the refractive index via a single numerical application of the inverse Fourier transform. These linear approaches are typically valid only for objects that are weakly scattering; their application on highly contrasted or large objects often results in images of poor spatial resolution.



Regularization is a standard approach for improving the resolution in optical diffraction tomography. It provides effective means for mitigating various artifacts and for suppressing noise. For example, Choi et al. [4] demonstrated that, under the straight-ray approximation, the missing cone artifact,which results in elongation of the reconstructed shape and underestimation of the value of the refractive index, can be significantly reduced by iteratively imposing positivity on the refractive index. The benefits of this iterative approach was further demonstrated in the weakly-scattering regime by Sung et al. [5]. In recent years, sparsity-promoting regularization,which is an essential component of compressive sensing theory [6], [7], has provided more dramatic improvements in the quality of tomographic imaging [8], [9]. The basic motivation is that many optical tomographic images are inherently sparse in some transform domain and can be reconstructed with high accuracy even with low amount of measured data.

In this paper, we present a novel iterative imaging method for optical tomography that combines sparsity-driven regularization with a nonlinear forward physical model of the propagation of the light-field. Specifically, our model is based on a popular technique in optics called beam propagation method (BPM), which is extensively used for modeling diffraction and propagation effects of light-waves [10]–[14]. Accordingly,BPM provides a more accurate model than its linear counterparts, especially when scattering effects cannot be neglected.Unlike other nonlinear alternatives, such as the ones based  on the coupled dioleapproximatio,16],BPM ha te advantage that it is reasonably fast to implement and that it can be efficiently optimized via a time-reversal scheme. This scheme allows to compute the derivative of the transmitted lightfldwcttotiuioofaciendex b simple error backpropagation.This allows us to develop a fast iterativealoihmbasedotchaticrioofthe proximalgradient descent that uses measurements in an online fashion and thus significantly reduces the memory requirements for the reconstruction. Our results demonstrate that the proposed method can reconstruct high-quality images of the refractive index even when missing significant amounts of data.

In our companion paper, we have presented the optical and conceptual aspects of our BPM-based imaging framework [17]. Here, we complement our initial report by providing the algorithmic details of the reconstruction and by presenting additional validations on simulated as well as on experimentally measured data. Our work is also related to the recent iterative optimization method by Tian and Waller [18]that was demonstrated for imaging 3D objects using incoherent illumination and intensity detection. The primary difference is that these authors use intensity measurements directly while our method relies on digital holography [19], [20] to record the complex amplitude of the field. The other improvement is on the signal processing side with the introduction of sparse regularization in order to achieve high-quality imaging with undersampled data. An interesting future work would beto see if the method proposed in this paper works for imaging phase objects directly from their intensity measurements.

This paper is organized as follows. In Section I, we present our forward model based on BPM. In Section III, we present our algorithmic framework for the recovery of the refractive index from the measurements of the light field. Specifically,our algorithm estimates the refractive index by minimizing a cost functional, where the data-term is based on BPM and the regularizer promotes solutions with a sparse gradient.Fundamentally, the algorithm relies on the computation of the derivatives of the forward model with respect to the refractive index, which will be presented in a great detail. In Section IV, we present some experimental results illustrating the performance of our algorithm on experimental as well as simulated data.



### I I. FORWARD MODEL 

This section presents the BPM forward model, whose complete derivation can be found in Appendix A. Although, BPM is a standard technique in optics for modeling propagation of light in inhomogeneous media [10]–[14], it is less known in the context of signal reconstruction and inverse problems. We shall denote our nonlinear forward model by $\mathbf{y}=\mathbf{S}(\mathbf{x})$ ,where the  vector $\mathbf{y}\;\in\;\mathbb{C}^{M}$ contains the samples of the measured light-field,$\mathbf{x}\in\mathbb{R}^{N}$ is the discretized version of the refractive index, and $\mathbf{S}:\mathbb{R}^{N}\to\mathbb{C}^{M}$ is the nonlinear mapping. Note that the nonlinearity of BPM refers to the relationship between the refractive index and the measured light-field, not to the relationship between input and output light-fields, which is linear.



$$u(x,y,L_{z})$$

<div style="text-align: center;">Fig.1. Visual representationof the scattering scenario considered in this paper. A sample with a real refractive index contrast $\delta n({\pmb r})$ is illuminated with an input light $u(x,y,z=0)$ , which propagates through the sample, and results in the light $\widehat{u(x,y,z)}=L_z$ at the camera plane. The light at the camera plane is holographically captured and the algorithm proposed here is used for estimating the refractive index contrast $\delta n(\mathbf{r})$ '</div>


### A. Fourier beam-propagation 

The scalar inhomogeneous Helmholtz equation implicitly describes the relationship between the refractive index and the light field everywhere in space.



$$\left(\Delta+k^{2}({\pmb r})\operatorname{I}\right)u({\pmb r})=0,$$

where $\boldsymbol{r}=(x,y,z)$ denotes a spatial position, u is the total light-fieldat1$\vec{r},\Delta=\left(\partial^{2}/\partial x^{2}+\partial^{2}/\partial y^{2}+\partial^{2}/\partial z^{2}\right)$ is the Laplacian, I is the identity operator, and $k(\mathbf{\mathit{r}})=\omega/c(\mathbf{\mathit{r}})$ is the wavenumber of the light field at r. The spatial dependence of the wavenumber k is due to variations of the speed of light c induced by the inhomogeneous nature of the medium under consideration. Specifically, the wavenumber in () can be decomposed as follows 



$$k({\bf r})=k_{0}n({\bf r})=k_{0}(n_{0}+\delta n({\bf r})),$$

where $k_{0}=\omega/c_{0}$ is the wavenumber in the free space, with $c_{0}\;\approx\;3\times10^{8}$ m/s being the speed of light in free space.The quantity n is the spatially varying refractive index of the sample, which we have written in terms of the refractive index  of  the  medium $n_{0}$ and the perturbation $\delta n$ due to inhomogeneities. We assume that the refractive index is real,which is an accurate approximation when imaging weakly absorbing objects such as biological cells.



BPM is a class of algorithms designed for calculating the optical field distribution in space or in time given initial conditions. By considering the complex envelope $a({\pmb r})$ of the paraxial wave $u({\boldsymbol{r}})\;=\;a({\boldsymbol{r}})\exp(\mathrm{j}k_{0}n_{0}z)$ ,one can develop BPM as an evolution equation for a in which $z\mathrm{p l a y s}$ :the role of evolution parameter 



$$\begin{aligned}{}&{{}a(x,y,z+\delta z)=\operatorname{e}^{\operatorname{j}k_{0}(\delta n(\mathbf{r}))\delta r_{z}}\times}\\ {}&{{}\mathcal{F}^{-1}\left\{\mathcal{F}\left\{a(\cdot,\cdot,z)\right\}\times\operatorname{e}^{-\operatorname{j}\left(\frac{\omega_{x}^{2}+\omega_{y}^{2}}{k_{0}n_{0}+\sqrt{k_{0}^{2}n_{0}^{2}-\omega_{x}^{2}-\omega_{y}^{2}}}\right)\delta z}\right\}.}\\ \end{aligned}$$

Therefore, BPM allows to obtain the wave-field in space via alternating evaluation of diffraction and refraction steps handled in the Fourier and space domains, respectively (see Appendix A for mode details).



It is important to note that BPM ignores reflections. This can be seen from the fact that if the solution exists for an 

<div style="text-align: center;"><img src="imgs/img_in_image_box_44_64_592_423.jpg" alt="Image" width="44%" /></div>


<div style="text-align: center;">Fig. 2. Propagation of a plane-wave of $\lambda=561$ nm in an immersion oil with $\overset{\frown}{n_{0}}=1.518$ simulated with BPM.$(a-c)$ Propagation in oil. (df) Immersion of a 10 m bead of $n=1.548.(a,d)x-y$ slice of the beam magnitude at $z=L_{z}/2.\;({\sf b},{\sf e})\;x{\mathrm{-}}y$ slice of the beam phase at $z=L_{z}/2.\;(\mathrm{c},\mathrm{f})\;x\mathrm{-}z$ slice of the beam magnitude at $y=0$ The circle in (f) illustrates the boundary of the bead at $y=0$ Scale bar,10 m. </div>


arbitrary initial condition $a_{0}\triangleq a(x,y,z=0)$ ,then $a_{0}$ does not depend on $a({\pmb r})$ .



### B. Numerical implementation 

We consider 3D volume $[-L_{x}/2,L_{x}/2]\quad\times$ $[-L_{y}/2,L_{y}/2]\times[0,L_{z}]$ that we refer to as computational domain. The domain is sampled with steps $\delta x,\;\delta y$ _,and $\delta z$ which will result in $N_{x},N_{y}$ ,and K samples, respectively. We will additionally use the following matrix-vector notations 

•x: samples of the refractive-index distribution $\delta n$ in the computational domain.



•y: samples of the complex light-field a.

•S: nonlinear forward operator that implements BPM and maps the refractive index distribution into the complex light-field $\mathbf{y}=\mathbf{S}(\mathbf{x})$ 



We use the index k to refer to the quantities described above at the kth slice along the optical axis z. For simplicity, we assume that all 2D quantities at the kth slice are stored in a vector. Then, given the initial input field $\mathbf{y}_{0}=\mathbf{S}_{0}(\mathbf{x})$ and the refractive index distribution x, the total field $\{\mathbf{y}_{k}\}_{k\in[1\ldots K]}$ can be computed recursively as follows 

$$\mathbf{S}_{k}(\mathbf{x})=\operatorname{d i a g}\left(\mathbf{p}_{k}(\mathbf{x}_{k})\right)\mathbf{H}\mathbf{S}_{k-1}(\mathbf{x}),$$

where the operator $\mathrm{d i a g}(\mathbf{u})$ creates a square matrix with the elements of the input vector u the main diagonal. The matrix H denotes the diffraction operator; it is implemented by taking the discrete Fourier transform (DFT) of the input field,multiplying it by a frequency-domain phase mask, and taking the inverse DFT. The vector $\mathbf{p}_{k}(\mathbf{x}_{k})=\exp(\mathrm{j}k_{0}\delta z\mathbf{x}_{k})$ ,which depends onththsliceof theactive index $\mathbf{x}_{k}$ , accounts for a phase factor corresponding to the implementation of the refraction step. Finally, the measured data y corresponds to the light-field at the Kth slice of the computational domain,i.e.,$\mathbf{y}{=}\mathbf{y}_{K}{=}\mathbf{S}_{K}(\mathbf{x})$ 1. Note that from (4), one can readily evaluate the computational complexity of BPM, which roughly corresponds to 2K evaluations of FFT or $O(N\operatorname{l o g}(\widetilde{N/K}))$ with $\overset{\circ}{N}=N_{x}N_{y}K$ 



Figure 2 ilustrates a simulation where a plane-waveof $\lambda=561$ .nm with a Gaussian amplitude is propagated in an immersion oil $n_{0}=1.518at\lambda=561$ nm) with an angle of $\pi/32$ with respect to the optical axis z. The computational domain of dimensions $L_{x}=L_{y}=L_{z}=36.86$ m is sampled with steps $\delta x=\delta y=\delta z=\overset{\circ}{144}$ : nm. In (a)—(c) we illustrate the propagation of the light-field in immersion oil, while in $(\mathsf{d})–(\mathsf{f})$ we illustrate the propagation when a spherical bead of diameter 10 m with refractive index $n=1.548$ is immersed in the oil. As we can see in (f) even for a relatively weak refractive index contrast of $\delta n=0.03$ , one can clearly observe the effects of scattering on the magnitude of the light-field.

### I II. PROPOSED METHOD 

In practice, the input field (b $\mathbf{y}_{0}$ is known and the output field $\mathbf{y}_{K}$ is measured using a holographic technique that gives access to the full complex-valued light-field. Our goal is to recover x from a set of L views $\{\mathbf{y}_{K}^{\ell}\}_{\ell\in[1\dots L]}$ corresponding to input fields $\{\mathbf{y}_{0}^{\ell}\}_{\ell\in[1\dots L]}$ . We shall denote with M the total number of measurements in a single view $\mathbf{y}^{\ell}$ and with N the total number of voxels in x.



### A. Problem formulation 

We formulate the reconstruction task as the following minimization problem 



$$\begin{aligned}{\widehat{\mathbf{x}}}&{{}=\mathop{\operatorname{a r g}\operatorname*{m i n}}_{\mathbf{x}\in\mathcal{X}}\left\{\mathcal{C}(\mathbf{x})\right\}}\\ {}&{{}=\mathop{\operatorname{a r g}\operatorname*{m i n}}_{\mathbf{x}\in\mathcal{X}}\left\{\mathcal{D}(\mathbf{x})+\tau\mathcal{R}(\mathbf{x})\right\},}\\ \end{aligned}$$

where D is the data-fidelity term and R is the regularization term to be discussed shortly. The convex set $\mathcal{X}\subseteq\widehat{\mathbb{R}^{N}}$ is used to enforce certain physical constraints on the refractive index such as its non-negativity. The parameter $\tau>0$ controls the amount of regularization.



The data fidelity term in (5) is given by 

$$\begin{aligned}{\mathcal{D}(\mathbf{x})\:\triangleq\:}&{{}\frac{1}{L}\sum_{\ell=1}^{L}\mathcal{D}_{\ell}(\mathbf{x})}\\ {\triangleq\:}&{{}\frac{1}{2L}\sum_{\ell=1}^{L}\left\|\mathbf{y}_{K}^{\ell}-\mathbf{S}_{K}^{\ell}(\mathbf{x})\right\|_{\ell_{2}}^{2},}\\ \end{aligned}$$

where L denotes the number of measured views. For a given view , the forward operator $\mathbf{S}_{K}^{\ell}$ can be computed recursively via equation (4).



As a regularization term in (5), we propose to use the 3D isotropic total variation (TV) [21] of the refractive index distribution 



$$\begin{aligned}{\mathcal{R}(\mathbf{x})}&{{}\triangleq\sum_{n=1}^{N}\|[\mathbf{D}\mathbf{x}]_{n}\|_{\ell_{2}}}\\ {}&{{}=\sum_{n=1}^{N}\sqrt{([\mathbf{D}_{x}\mathbf{x}]_{n})^{2}+([\mathbf{D}_{y}\mathbf{x}]_{n})^{2}+([\mathbf{D}_{z}\mathbf{x}]_{n})^{2}}.}\\ \end{aligned}$$

where D:$\mathbb{R}^{N}\:\to\:\mathbb{R}^{N\times3}$ is the discrete counterpart of the gradient operator. The matrices $\mathbf{D}_{x},\mathbf{D}_{y}$ ,and $\mathbf{D}_{z}$ denote the finite difference operations along the x, y, and z directions,

Algorithm 1 Time-reversal scheme for computing $\mathbf{\nabla}\mathcal{D}^{\tilde{H}}$ input: input field y0, output field y ,and current estimate of the refractive-index distribution x.output: the gradient [∇D(x]H.
algorithm:1) Compute the total field y = S(x) using the BPM recursion (4), keeping all the intermediate light-fields yk = Sk(x) in memory.
2) Compute the residual r = yK −yκ and set sK =0.3) Compute s0 =SK(x)] H rK using thefollowing iterative procedure for m = K, . . . , 1a)Sm−1=+[pm)]dg1m b) rm−1 = HH dig (pm(xm)) m 4) Return [∇D(x)]H = Re{s0}.

respectively (see Appendix B for more details). The TV prior on images has been originally introduced by Rudin et al. [21] as a regularization approach capable of preserving image edges, while removing noise. It is often interpreted as a sparsity-promoting 1-penalty on the magnitudes of the image gradient [22]. TV regularization has proven to be successful in a widerangeof applications in thecontextof sparse recovery of images from incomplete or corrupted measurements [6],[23].



The minimization in (5) is a nontrivial optimization task.Keepin ilid in the fact that the data term D is based on a nonlinear forward operator S. The other challenging aspects are the massive quantity of data that need to be processed and the presence of a nonsmooth regularization term R. We next present a novel algorithm based on iterative stochastic proximal-gradient descend that is made tractable via the time-reversal scheme that allows for an efficient computation of the gradient of D with respect to x.



### B. Computation of the gradient 

The crucial component of our method is recursive computation of the gradient of D with respect to X, summarized in Algorithm 1, which is explained next. For notational simplicity, we consider the scenario of a single view and thus drop the indices  from the subsequent derivations. The generalization of the final formula to an arbitrary number of views L is straightforward.



We start by expanding the quadratic term as 

$$\begin{aligned}{}&{{}\mathcal{D}(\mathbf{x})=\frac{1}{2}\|\mathbf{y}_{K}-\mathbf{S}_{K}(\mathbf{x})\|_{\ell_{2}}^{2}\quad(9)}\\ {}&{{}=\frac{1}{2}\langle\mathbf{y}_{K},\mathbf{y}_{K}\rangle-\operatorname{R e}\left\{\langle\mathbf{S}_{K}(\mathbf{x}),\mathbf{y}_{K}\rangle\right\}+\frac{1}{2}\langle\mathbf{S}_{K}(\mathbf{x}),\mathbf{S}_{K}(\mathbf{x})\rangle,}\\ \end{aligned}$$

where $\langle\mathbf{x},\mathbf{z}\rangle\:=\:\mathbf{z}^{H}\mathbf{x},$ , where the Hermitian transposition H is due to the complex nature of the quantities. We adopt the convention 

$$\frac{\partial}{\partial x_{j}}\mathbf{S}(\mathbf{x})=\left[\begin{array}{c}{\frac{\partial}{\partial x_{j}}[\mathbf{S}(\mathbf{x})]_{1}}\\ {\vdots}\\ {\frac{\partial}{\partial x_{j}}[\mathbf{S}(\mathbf{x})]_{M}}\\ \end{array}\right].$$

Then, the gradient is given by 

$$\begin{aligned}{\mathbf{\nabla}\mathcal{D}(\mathbf{x})}&{{}=\left[\frac{\partial \mathcal{D}(\mathbf{x})}{\partial x_{1}}\ldots\frac{\partial \mathcal{D}(\mathbf{x})}{\partial x_{N}}\right]}\\{}&{{}=\operatorname{Re}\left\{\left(\mathbf{S}_{K}(\mathbf{x})-\mathbf{y}_{K}\right)^{H}\left[\frac{\mathbf{\partial }}{\mathbf{\partial x}}\mathbf{S}_{K}(\mathbf{x})\right]\right\},}\\\end{aligned}$$

where 

$$\begin{aligned}{\frac{\partial}{\partial\mathbf{x}}\mathbf{S}_{K}(\mathbf{x})}&{{}=\left[\frac{\partial}{\partial x_{1}}[\mathbf{S}_{K}(\mathbf{x})]\ldots\frac{\partial}{\partial x_{N}}[\mathbf{S}_{K}(\mathbf{x})]\right]}\\ {}&{{}=\left[\begin{array}{c c c}{\frac{\partial}{\partial x_{1}}[\mathbf{S}_{K}(\mathbf{x})]_{1}}&{\ldots}&{\frac{\partial}{\partial x_{N}}[\mathbf{S}_{K}(\mathbf{x})]_{1}}\\ {\vdots}&{\vdots}&{\vdots}\\ {\frac{\partial}{\partial x_{1}}[\mathbf{S}_{K}(\mathbf{x})]_{M}}&{\ldots}&{\frac{\partial}{\partial x_{N}}[\mathbf{S}_{K}(\mathbf{x})]_{M}}\\ \end{array}\right].}\\ \end{aligned}$$

In practice, we are interested in a column vector 

$$\left[\mathbf{\nabla}\mathcal{D}(\mathbf{x})\right]^{H}=\operatorname{R e}\left\{\left[\frac{\partial}{\partial\mathbf{x}}\mathbf{S}_{K}(\mathbf{x})\right]^{H}\left(\mathbf{S}_{K}(\mathbf{x})-\mathbf{y}_{K}\right)\right\}.$$

Therefore, we need to derive a tractable algorithm to compute (13). The recursive BPM formula (4) allows us to write 

$$\begin{aligned}{\frac{\partial}{\partial\mathbf{x}}\mathbf{S}_{k}(\mathbf{x})}&{{}=\frac{\partial}{\partial\mathbf{x}}\left[\operatorname{d i a g}\left(\mathbf{p}_{k}(\mathbf{x}_{k})\right)\mathbf{H}\;\mathbf{S}_{k-1}(\mathbf{x})\right]}\\ {}&{{}=\operatorname{d i a g}\left(\mathbf{H}\;\mathbf{S}_{k-1}(\mathbf{x})\right)\left[\frac{\partial}{\partial\mathbf{x}}\mathbf{p}_{k}(\mathbf{x}_{k})\right]}\\ {}&{{}\qquad+\operatorname{d i a g}\left(\mathbf{p}_{k}(\mathbf{x}_{k})\right)\mathbf{H}\left[\frac{\partial}{\partial\mathbf{x}}\mathbf{S}_{k-1}(\mathbf{x})\right].}\\ \end{aligned}$$

Then, we have the following equality 

$$\begin{aligned}{}&{{}\left[\frac{\partial}{\partial\mathbf{x}}\mathbf{S}_{k}(\mathbf{x})\right]^{H}}\\ {}&{{}=\left[\frac{\partial}{\partial\mathbf{x}}\mathbf{S}_{k-1}(\mathbf{x})\right]^{H}\mathbf{H}^{H}{\operatorname{d i a g}}\left(\overline{{\mathbf{p}_{k}(\mathbf{x}_{k})}}\right)}\\ {}&{{}\qquad+\left[\frac{\partial}{\partial\mathbf{x}}\mathbf{p}_{k}(\mathbf{x}_{k})\right]^{H}{\operatorname{d i a g}}\left(\overline{{\mathbf{H}\;\mathbf{S}_{k-1}(\mathbf{x})}}\right),}\\ \end{aligned}$$

where the vector v contains complex conjugated elements of vector v. Also, note that since the input field is known and does not depend on x, for $k=0$ ,we have 

$$\left[\frac{\partial}{\partial\mathbf{x}}\mathbf{S}_{0}(\mathbf{x})\right]^{H}=\mathbf{0}.$$

Based on the recursion (14) with the boundary condition (15),we obtain a practical implementation of (13), which is summarized in Algorithm 1. Conceptually, our method is similar to the error backpropagation algorithm extensively used in deep learning for neural networks [24]. Similarly, to backpropagation, we compute the gradient by propagating the error in a time-reversed fashion. Computational complexity of the timereversal scheme is of the same order as that of BPM and essentially corresponds to a constant number of K FFTs of $N_{x}\times N_{y}$ images.



Algorithm 2 Minimizes:$\mathcal{C}(\mathbf{x})=\mathcal{D}(\mathbf{x})+\tau\mathcal{R}(\mathbf{x})$ 
{γ$\tau>0$ ,an itial gess $\widehat{\mathbf{x}}^{0}$ )er $\tilde{L}\in$ 不
[1.. . L].

set: t ←1, s0←x0, q0 ← 1
repeat 

et $\tilde{L}$ 
views. We index them with {i}i∈[1.….L]
Zt ← st−1 − (γt/L) ∑i=L ∇dD(cid:18:1)
xt ← proxR(zt,γtτ )

$qt ←$\fra{}{}$(1 + √1 + 4q2−1
st ← xt + ((qt−1 − 1)/qt)(xt − xt−1)
t ←t + 1

until stopping criterion 

return estimate of the refractive index xt 

### C. Iterative reconstruction 

By relying on the time-reversal scheme, we propose a novel algorithm, summarized in Algorithm 2, that reconstructs the refractive index x from optical tomographic measurements $\{\mathbf{y}_{K}^{\ell}\}_{\ell\in[1\dots L]}$ . Conceptually, the algorithm is similar to the fast iterative shrinkage/thresholding algorithm (FISTA) [25],which is a popular approach for minimizing cost-functions that consist of sums between smooth and nonsmooth terms.One notable difference of Algorithm 2 with respect to FISTA,summarized in Algorithm 3 of Appendix B is that the gradient is only computed with respect to $\tilde{L}\leq L$ measurements selected with equal probability, at each iteration, from the complete set of measurements $\{\mathbf{y}_{K}^{\ell}\}_{\ell\in[1\dots L]}$ For $\tilde{L}\;\ll\;L$ ,this incremental proximal-gradient approach [26] reduces the per-iteration cost of reconstruction significantly; moreover,since gradient computation for our BPM model is highly parallelizable the number $\tilde{L}$ can be adapted to match the number of available processing units. Also, the overall convergence of Algorithm 2 can be substantially faster to that of full FISTA in Algorithm 3. To understand this consider an example where the measured views of the object are the same or very similar. Then, the partial gradient in Algorithm 2will require $(L{-}\tilde{L})$ times less computation, but will still point to the right direction. A more detailed discussion on the benefits of incremental algorithms for solving very large scale optimization problems can be found in the recent work by Bertsekas [26].



A crucial step in Algorithm 2 is the proximal operator for the regularizer R 



$$\operatorname{p r o x}_{\mathcal{R}}(\mathbf{z},\tau)\triangleq\operatorname*{a r g\operatorname*{m i n}}_{\mathbf{x}\in\mathcal{X}}\left\{\frac{1}{2}\|\mathbf{x}-\mathbf{z}\|_{\ell_{2}}^{2}+\tau\mathcal{R}(\mathbf{x})\right\}.$$

The proximal operator corresponds to the regularized solution of the denoising problem with the forward operator corresponding to identity. Note that although our proximal operator for 3D TV regularizer does not admit aclosed form, it can be efficiently computed [25], [27]–[29]. Here, we rely on the dual minimization approach that was proposed by Beck and Teboulle [25], which we review in Appendix B and summarize in Algorithm 4.



<div style="text-align: center;"><img src="imgs/img_in_chart_box_643_78_1162_345.jpg" alt="Image" width="42%" /></div>


<div style="text-align: center;">Fig. 3. Evolution of the cost $\mathcal{C}(\widehat{\mathbf{x}}^{t})$ during the reconstruction over 1000iterations for a 10 m bead in immersion oil. </div>


The theoretical convergence of our algorithm is difficult to analyze due to nonlinear nature of S. However, in practice, we found that by providing the algorithm with a warm initialization and by setting the steps of the algorithm $\gamma_{t}$ proportional to $1/\sqrt{t}$ ,the algorithm achieves excellent results as reported in Section IV. The progressive reduction in $\gamma_{t}$ is commonly done for ensuring the convergence of incremental proximal-gradient algorithms [26]. One practical approach for finding a warm initializer is to use the standard FBP algorithm that assumes a straight ray approximation. When imaging semi-transparent objects such as cells, even simpler but sufficient initialization is a constant value. Additionally, we fix the maximal number of iterations for the algorithm to $t_{\mathrm{m a x}}$ and select an additional stopping criterion based on measuring the relative change of the solution in two successive iterations as 

$$\frac{\|\widehat{\mathbf{x}}^{t}-\widehat{\mathbf{x}}^{t-1}\|_{\ell_{2}}}{\|\widehat{\mathbf{x}}^{t-1}\|_{\ell_{2}}}\leq\delta,$$

where we use $\delta=10^{-4}$ in all the experiments.

### I V. NUMERICAL EVALUATION 

Based on the above developments, we report the results of our iterative reconstruction algorithm in simulated and experimental configurations. The specifics of our experimental setup were discussed in the companion paper [17]. Essentially,the setup is holographic, which means that a laser source of $\lambda=561$ . nm is split into the reference and sample beams that are combined into a hologram, which is subsequently used to extract the complex light field at the measurement plane [30].

We first tested our BPM-based reconstruction algorithm on simulated data. In particular, we considered the reconstruction of a simple 10 m bead of refractive index $n~=~1.548$ ;immersed into oil of refractive index $n_{0}\quad=\quad1.518$ .We simulated $L=61$ . measurements with equally spaced angles in $[-\pi/8,\pi/8]$ with BPM. The illumination beam is tilted perpendicular to the y axis, while the angle is specified with respect to the optical axis z. The dimension of computational domain is set to $L_{x}\:=\:L_{y}\:=\:36.86$ m and $L_{z}\:=\:18.45$ 1m and it is sampled with steps $\delta x=\delta y=\delta z=144$ nm.The reconstruction is performed via the proposed approach in Algorithm 2 with $\mathcal{X}=\{\mathbf{x}\in\mathbb{R}^{N}:0\leq\hat{\mathbf{x}}\leq0.1\},$ $\tilde{L}=8$ and $\tau~=~0.01$ .. In Figure 3, we illustrate the convergence of the algorithm by ploting the cost C for 1000 iterations.In Figure 4, we show the true and reconstructed refractive 

<div style="text-align: center;"><img src="imgs/img_in_image_box_33_18_1126_378.jpg" alt="Image" width="89%" /></div>


<div style="text-align: center;">Fig.6. Reconstruction with a proposed method of a $37\times37\times30$ m sample containing a HeLa cell for various values of the data-reduction factor.$(a-c)$ Reconstructionwitaintpitandostivity.Rconstructiononlwtpoitivitya,d2×datrducto.b,×daion.$(\mathrm{c},\mathrm{f})\;32\times$ ;data reduction. Right panel shows the SNR (see text) versus the data-reduction factor for both priors.Scale bar, 10 m.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_24_510_577_867.jpg" alt="Image" width="45%" /></div>


<div style="text-align: center;">Fig. 4. Reconstruction of a 10 m bead of refractive index 1.548 in an immersion oil with $n_{0}=1.518$ from BPMsimulatedmeasurements.(ad) True refractive index distribution.(e—h) Reconstructed refractive index distribution:$\mathrm{{\sf{S N R}}=22.74}$ dB. (a, e) A 3D rendered image of the bead.(b, f) x-y slice of the bead at $z=L_z/2.(c,g)z-x$ slice of the bead at $y=0.(\mathrm{d},\mathrm{h})z\mathrm{-}y$ 一$y=0.(\mathrm{d},\mathrm{h})z\mathrm{-}y$ slice of the bead at $x=0$ Scale bar, 10 m.</div>


<div style="text-align: center;">Fig. 5. Reconstruction of a 10 m bead of refractive index 1.588 in an immersion oil with $n_{0}\;=\;1.518$ from experimentally measured data. (ad) Reconstruction using our algorithm. (e—h) Reconstruction using the FBP algorithm. (a, e) A 3D rendered image of the bead. (b, f) x-y slice of the bead at $z=21.17$ m.(c, g)z-x slice of the bead at $y=-2.30$ | m. (d,h) z-y slice of the bead at $x=0.58$ m. Scale bar, 10 m.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_627_1045_1165_1205.jpg" alt="Image" width="43%" /></div>


<div style="text-align: center;">Fig.7. Comparison of the proposed method on a HeLa cell when applying the proximal operator (a) at every iteration, (b) only once at the end for denoising purposes. The proximal operator imposes sparsity on the gradient of the image. This figure illustrates the benefits of imposing sparsity which influences the convergence to a better solution. Scale bar,10 m.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_625_510_1168_866.jpg" alt="Image" width="44%" /></div>


index distributions. The final signal-to-noise ratio (SNR) of the solution is 22.74 dB. The visual quality of the reconstruction is excellent; we can observe that on simulated data, the method corrects the missing cone due to limited angle of illumination and yields a sharp image along the z-axis.



We next validate the BPM forward model and our reconstruction algorithm on a similar dataset that was obtained experimentally. The sample is a 10 m polystyrene bead of refractive index $n\quad=\quad1.588$ immersed in oil with a refractive index of $n_{0}=1.518$ ;so that the refractive indx contrast is $\delta n=0.07$ . The data was obtained by collecting $L=61$ .measurements with equally spaced angles in the range $[-32.16^{\circ},30.80^{\circ}]$ |. We perform reconstruction with the regularization parameter $\tau=10$  In Figure 5 (a)–(d), we shw the result that was obtained by initializing our algorithm with the solution of the standard FBP performed on the phase of the measured wave field. The FBP approach assumes a straight ray approximation and its results are illustrated in Figure 5 (e)–(h).Note that such a warm initialization is useful due to the nonconvex nature of our optimization problem. In the $x{-}y$ slice at $z\:=\:21.17$ m, the bead reconstructed with our method has the diameter of approximately 10.08 m and an average refractive index of 0.067. As we can see, one of the major benefits of using the proposed method is the correction of the missing cone that is visible in Figures 5 (g) and (h).

<div style="text-align: center;"><img src="imgs/img_in_image_box_69_37_1158_751.jpg" alt="Image" width="88%" /></div>


<div style="text-align: center;">Fig.ottut $37\times37\times30$ m containing a HeLa cell. (a−c)Proposedho.tieiobarhtapio.ittiuciooioaph1].(a,d)2×ducioducoi×drucioclebam. </div>


Next, we investigated the ability of our method to re construct real biological samples from limited amounts of data. Specifically, we illuminated a sample containing a HeLa cell at 161 distinct angles uniformly distributed in the range $\left[-45^{\circ},45^{\circ}\right]$ . The data was used for imaging a volume of size $\stackrel{\circ}{3}7\times37\times\stackrel{\circ}{30}\mu\mathrm{m}\;(\delta x=\delta y=\delta z=72\;\mathrm{n m})$ 1. In this experiment,the data-reduction or undersampling factor refers to the ratio between the total number of holograms 161 and the actual number used for reconstruction. In particular, data-reduction factors 2,4,8,16, and 32 correspond to 81,41,21,11, and 6holograms used for reconstruction, respectively. We illustrate the reconstruction results in Figure 6, where we compare the results of the proposed BPM–based method with and without TV regularization. We again initialize the algorithms with the volume that was obtained by running the standard FBP algorithm that assumes straight ray propagation. However,we observed that the algorithm is robust in the sense that it typically converges to the same solution independently of the initializer (also see Fig. 6 from our companion paper [17]). To quantify the quality of the reconstructed volume as a function of data-reduction factor, we also defined 

$$\mathrm{SNR}(\mathrm{dB})\triangleq10\log_{10}\left(\frac{\|\mathbf{x}_{\mathrm{ref}}\|_{\ell_2}^2}{\|\mathbf{x}_{\mathrm{ref}}-\widehat{\mathbf{x}}\|_{\ell_2}^2}\right),$$

where $\mathbf{x}_{ref}$ is the reconstructed volume from all the 161 possible measurements. The right panel of Figure 6 illustrates the evolutio of NR wi uamli aA can e see the sparse-regularization plays a critical role and significantly boosts the quality of the solution at all undersampling rates.Also note that the result in Figure 6 (c) was obtained by using only 6 holograms of size $512\times512$ for reconstructing a signal of size $512\times512\times400$ voxels, which corresponds to data-toparameter ratio of 1.5/100.



In Figure 7, we highlight the importance of sparsity-driven iterative reconstruction. Specifically, we compare our algorithm, where the TV proximal operator is applied at each iteration, against an algorithm that first reconstructs the refractive index only with positivity constraints and then applies 3D TV denoising to the final result. Although, both algorithm rely on BPM, by imposing the gradient sparsity at every iteration our algorithm converges to a visibly higher-quality solution.

In Figure 8, we compare the performance of our algorithms against two standard iterative algorithms that are commonly used in practice. The first one, whose results are shown in Figure 8 (d)–(f), is based on the algorithm that was proposed by Choi et al. [4]. It assumes a straight ray propagation of the light through the medium and iteratively minimizes the quadratic distance between the true and predicted phase measurements under positivity constraints. This iterative approach is an improvement over FBP and was shown to yield high quality results when imaging biological samples [4]. The second method, whose results are shown in Figure 8 (g)—(i, was proposed by Kim et al.[31] and is based on iterative diffractotacion tomography improves over the straight ray approximation by incorporating diffraction effects due to inhomogeneities in the sample into the forward model. As can be seen, our proposed method yields sharper and higher-quality images with a significant reduction in the missing cone artifacts.

### V. CONCLUSION 

We have presented a novel computational method for the estimation of the refractive index distribution of a 3D object from the measurements of the transmitted light-field. Our method relies on a nonlinear forward model, which is based on simulating the physical propagation of electromagnetic waves with BPM. We compensated the ill-posedness of the inverse problem, by imposing positivity as well as the gradientsparsity to the solution. The method is computationally efficient due to the time-reversal scheme for computing the gradients and the fact that only a subset of gradients are evaluated at every iteration. Overall, we believe that our approach opens rich perspectives for high-resolution tomographic imaging in a range of practical setups. We have demonstrated the use of the method for experimentally reconstructing a polystyrene bead as well as a HeLa cell immersed in oil and water, respectively.Even when the number of measurements is severely restricted,the method can recover images of surprisingly high-quality.

There are several limitations that may be addressed in future work. Although, in practice, we did not encounter any convergence problems, the nonlinear nature of the forward model makes the theoretical convergence of the method difficult to analyze. Since the proposed BPM optimization scheme is similar to the error backpropagation algorithm used for training deep neural networks [32], there may be some benefit in transposing the analysis techniques that are being rapidly developed there to our framework.



In our current experimental setup the measurements are obtained by only changing the illumination angle. However,our forward model can handle arbitrary illumination patterns.This makes it much more general than its linear counterparts that are based on Radon or on diffraction tomography. Accordingly, another avenue of work would be to investigate the performance of the proposed method under different and less standard types of illumination.



## APPENDIX A FOURIER BEAM-PROPAGATION METHOD 

In this section, we present the full derivation that supports the use of BPM as a forward model. We start by introducing the inhomogeneous Helmholtz equation that completely characterizes the light field at all spatial positions in a timeindependent form [33]. We then describe the important paraxial simplification of the Helmholtz equation, which is often used for describing the propagation of electromagnetic waves.Note that the derivations here are based on the paraxial version of BPM, which is simpler to derive, but is slightly less accurate thatthenonparaxialversion[34] usedin(3).While,an extensive discussion on the merits and drawbacks of either version is beyond the scope of this paper, both versions are sufficiently accurate to be used in the experiments presented here.



### A. Paraxial Helmholtz equation 

Our starting point is the scalar inhomogeneous Helmholtz equation 



$$\left(\Delta+k^{2}({\boldsymbol{r}})\mathrm{I}\right)u({\boldsymbol{r}})=0,$$

where $\boldsymbol{r}=(x,y,z)$ denotes a spatial position, u is the total light-field at r,$\Delta=\left(\partial^{2}/\partial x^{2}+\partial^{2}/\partial y^{2}+\partial^{2}/\partial z^{2}\right)$ isthe Laplacian, I is the identity operator, and $k({\bf r})=\omega/c({\bf r})$ is the wavenumber of the light field at r. Equation (1) implicitly describes the relationship between the refractive index and the light field everywhere in space. The spatial dependence of the wavenumber k is due to variations of the speed of light c induced by the inhomogeneous nature of the medium under consideration. Specifically, the wavenumber in (1) can be decomposed as follows 



$$k({\bf r})=k_{0}n({\bf r})=k_{0}(n_{0}+\delta n({\bf r})),$$

where $k_{0}=\omega/c_{0}$ is the wavenumber in the free space, with $c_{0}\;\approx\;3\times10^{8}$ m/s being the speed of light in free space.The quantity n is the spatially varying refractive index of the sample, which we have written in terms of the refractive index  of  the  medium $n_{0}$ and the  perturbation $\delta n$ due to inhomogeneities. We next develop the paraxial Helmholtz equation for the complex envelope $a({\pmb r})$ of the paraxial wave1

$$u(\boldsymbol{r})=a(\boldsymbol{r})\mathrm{e}^{\mathrm{j}k_{0}n_{0}z}.$$

One way to interpret (18) is to say that it corresponds to a plane wave propagating along z in the medium, modulated by the complex amplitude a. Now consider 

$$\begin{aligned}{}&{{}\frac{\partial^{2}}{\partial z^{2}}u(\boldsymbol{r})\quad(19)}\\ {}&{{}\quad{=}\frac{\partial}{\partial z}\left(\left(\frac{\partial a(\boldsymbol{r})}{\partial z}\right)\mathrm{e}^{\mathrm{j}k_{0}n_{0}z}+\mathrm{j}k_{0}n_{0}a(\boldsymbol{r})\mathrm{e}^{\mathrm{j}k_{0}n_{0}z}\right)}\\ {}&{{}\quad{=}\mathrm{e}^{\mathrm{j}k_{0}n_{0}z}\left(\frac{\partial^{2}a(\boldsymbol{r})}{\partial z^{2}}+2\mathrm{j}k_{0}n_{0}\left(\frac{\partial a(\boldsymbol{r})}{\partial z}\right)-k_{0}^{2}n_{0}^{2}a(\boldsymbol{r})\right).}\\ \end{aligned} 9)$$

By using this expression and substituting (18) into (), we obtain 



$$\begin{aligned}{}&{{}\left(\Delta+k^{2}(\mathbf{r})\operatorname{I}\right)\:u(\mathbf{r})}\\ {}&{{}=\left(\Delta_{\perp}+\frac{\partial^{2}}{\partial z^{2}}+2\operatorname{j}k_{0}n_{0}\frac{\partial}{\partial z}-k_{0}^{2}n_{0}^{2}\operatorname{I}+k^{2}(\mathbf{r})\operatorname{I}\right)}\\ {}&{{}\quad\times a(\mathbf{r})\operatorname{e}^{\operatorname{j}k_{0}n_{0}z}}\\ {}&{{}=\left(\Delta_{\perp}+\frac{\partial^{2}}{\partial z^{2}}+2\operatorname{j}k_{0}n_{0}\frac{\partial}{\partial z}+2k_{0}^{2}n_{0}\delta n(\mathbf{r})\operatorname{I}+k_{0}^{2}(\delta n(\mathbf{r}))^{2}\operatorname{I}\right)}\\ {}&{{}=0}\\ \end{aligned}$$

(i.$^1\mathrm{A}$ when sir $\mathfrak{n}(\theta)\approx\theta$ withintheditanceofawavlengh,othatthe waveapproximatlymains its underlying plane-wave nature.is valid). The variation of a with position must be slow 

where $\Delta_{\perp}=(\partial^{2}/\partial x^{2}+\partial^{2}/\partial y^{2})$ is the transverse Laplacian.We now introduce two simplifications.The first is the slowly varying envelope approximation (SVEA), which is valid when $|(\partial^{2}/\partial z^{2})a|\ll|k_{0}n_{0}(\partial/\partial z)a|$ and which allows us to suppress the second derivative of a in z [33], [35].In the second simplification, we ignore te term $(\delta n)^{2}$ .We thus obtain 

$$\frac{\partial}{\partial z}a(\boldsymbol{r})=\left(\mathrm{j}\frac{1}{2k_{0}n_{0}}\Delta_{\perp}+\mathrm{j}k_{0}\delta n(\boldsymbol{r})\mathrm{I}\right)a(\boldsymbol{r}).$$

Equation (21) is the slowly varying envelope approximation of the Helmholtz equation and is often referred to as the paraxial Helmholtz equation [35].



### B. Fourier beam-propagation 

BPM is a class of algorithms designed for calculating the optical field distribution in space or in time given initial conditions [14]. The paraxial Helmholtz equation (21) is an evolution equation in which the space coordinate z plays the role of evolution parameter.



We start by rewriting (21) in the operator form 

$$\frac{\partial}{\partial z}a(\boldsymbol{r})=\mathrm{D}\{a\}(\boldsymbol{r})+\mathrm{N}\{a\}(\boldsymbol{r}),$$

where 

$$\mathrm{D}\triangleq\mathrm{j}\frac{1}{2k_{0}n_{0}}\Delta_{\perp}\quad\mathrm{a n d}\quad\mathrm{N}\triangleq\mathrm{j}k_{0}\delta n(\boldsymbol{r})\mathrm{I}.$$

Note that the operator D is linear and translation-invariant (LTI), while the operator N corresponds to a pointwise multiplication.Thesolutioof2)atsuficietl mal $z=\delta z$ may be written formally as a complex exponential2

$$a(x,y,\delta z)=\operatorname{e}^{(\operatorname{D}+\operatorname{N})\delta z}a(x,y,0).$$

The operators $\exp(\mathrm{D}z)$ and $\exp(\mathrm{N}z)$ do a priori not commute;however, Baker-Campbell-Hausdorff formula [36] can be applied to show that the error from treating them as if they do will be of order $\delta z^{2}$ if we are taking a small but a finite z step $\delta z$ . This suggests the following approximation 

$$a(x,y,z+\delta z)=\mathrm{e}^{\mathrm{N}\delta z}\mathrm{e}^{\mathrm{D}\delta z}a(x,y,z).$$

Now, it is possible to get explicit expressions for the diffraction $\operatorname{e x p}(\operatorname{D}\delta z)$ and refraction $\exp(\mathrm{N}\delta z)$ operators, since they are independent. Diffraction is handled in the Fourier domain as 

$$a(\omega_{x},\omega_{y},z+\delta z)=\operatorname{e}^{-\mathsf{j}\frac{\omega_{x}^{2}+\omega_{y}^{2}}{2k_{0}n_{0}}\delta z}a(\omega_{x},\omega_{y},z),$$

which can also be expressed, for a fixed z, with a 2D Fourier filtering formula 



$$\begin{aligned}&a(x,y,z+\delta z)\\&=\mathcal{F}^{-1}\left\{\mathcal{F}\left\{a(\cdot,\cdot,z)\right\}\times\mathrm{e}^{-\mathrm{j}\frac{\omega_x^2+\omega_y^2}{2k_0n_0}\delta z}\right\}.\\ \end{aligned}$$

For refraction, we get 

$$a(x,y,z+\delta z)=\mathrm{e}^{\mathrm{j}k_{0}(\delta n(\mathbf{r}))\delta z}a(x,y,z),$$

2Note that for an operator T. we define a new operator $\mathbf{e}^{\mathrm{T}z}$ in terms of series expansion $\mathrm{e}^{\mathrm{T}z}\triangleq\sum_{n=0}^{\infty}{\frac{z^{n}}{n!}}\mathrm{T}^{n}$ . Therefore,for $a({\pmb r})$ ,we write 

$\begin{array}{r}{\mathrm{e}^{\mathrm{T}z}\{a\}(\boldsymbol{r})=\sum_{n=0}^{\infty}\frac{z^{n}}{n!}\mathrm{T}^{n}\{a\}\stackrel{n=0}{(\boldsymbol{r})}}\end{array}$ 



which amounts to a simple multiplication with a phase mask in the spatial domain.



A more refined version of BPM for simulating waves propagating at larger angles was derived by Feit and Flack [34]. By relying on their results, we can replace the diffraction step (26)by a more accurate alternative 



$$\begin{aligned}&a(x,y,z+\delta z)\quad(2)\\&=\mathcal{F}^{-1}\left\{\mathcal{F}\left\{a(\cdot,\cdot,z)\right\}\times\mathrm{e}^{-\mathrm{j}\left(\frac{\omega_x^2+\omega_y^2}{k_0n_0+\sqrt{k_0^2n_0^2-\omega_x^2-\omega_y^2}}\right)\delta z}\right\}.\\ \end{aligned} 28)$$

Our practical implementation in Section I-B relies on this nonparaxial version of BPM.



## APPENDIX B TOTAL VARIATION MINIMIZATION 

In this section, we discuss the concepts and algorithms behind total variation (TV) regularized image reconstruction (5).The material presented here is the review of the ideas that were originally developed by Beck and Teboulle in [25].

### A. Two variants of TV 

Two common variants of TV are anisotropic TV regularizer 

$$\begin{aligned}{\mathcal{R}(\mathbf{x})}&{{}\triangleq\sum_{n=1}^{N}\|[\mathbf{D}\mathbf{x}]_{n}\|_{\ell_{1}}}\\ {}&{{}=\sum_{n=1}^{N}(|[\mathbf{D}_{x}\mathbf{x}]_{n}|+|[\mathbf{D}_{y}\mathbf{x}]_{n}|+|[\mathbf{D}_{z}\mathbf{x}]_{n}|).}\\ \end{aligned}$$

and isotropic TV regularizer 

$$\begin{aligned}{\mathcal{R}(\mathbf{x})}&{{}\triangleq\sum_{n=1}^{N}\|[\mathbf{D}\mathbf{x}]_{n}\|_{\ell_{2}}}\\ {}&{{}=\sum_{n=1}^{N}\sqrt{([\mathbf{D}_{x}\mathbf{x}]_{n})^{2}+([\mathbf{D}_{y}\mathbf{x}]_{n})^{2}+([\mathbf{D}_{z}\mathbf{x}]_{n})^{2}}}\\ \end{aligned}$$

Here,$\mathbf{D}\::\:\mathbb{R}^{N}\:\to\:\mathbb{R}^{N\times3}$ is the discrete gradient operator,with matrices $\mathbf{D}_{x},\:\mathbf{D}_{y}$ ,and $\mathbf{D}_{z}$ denoting the finite difference operators along x, y, and z, respectively. Assuming columnwise vectorization of a 3D matrix of size $N_{y}{\times}N_{x}{\times}N_{z}$ :,which represents the 3D image, the gradient of x at position $n\in[1,\ldots,N]$ is given by 



$$[\mathbf{D}\mathbf{x}]_{n}=\left(\begin{matrix}{[\mathbf{D}_{x}\mathbf{x}]_{n}}\\ {[\mathbf{D}_{y}\mathbf{x}]_{n}}\\ {[\mathbf{D}_{z}\mathbf{x}]_{n}}\\ \end{matrix}\right)=\left(\begin{matrix}{\frac{x_{n+N_{y}}-x_{n}}{\delta x}}\\ {\frac{x_{n+1}-x_{n}}{\delta y}}\\ {\frac{x_{n+N_{x}N_{y}}-x_{n}}{\delta z}}\\ \end{matrix}\right),$$

with appropriate boundary conditions (periodization, Neumann boundary conditions, etc.). The constants $\delta x,\delta y$ ,and $\delta z$ denote ami i o,$y,$ ,and z directions, resetivel.lf $\mathrm{TV},$  often assume uniform sampling by setting $\delta x=\delta y=\delta z$ 



The anisotropic TV regularizer (29) can be interpreted as a sparsity-promoting $\ell_{1}$ -penalty on the image gradient,while its isotropic counterpart (30) as an $\ell_{1}\mathtt{-p e n a l t y}$ on the 

Algorithm 3 FISTA 

input: light-field data $\{\mathbf{y}^{\ell}\}_{\ell\in[1\dots L]}$ , initial guess $\widehat{\mathbf{x}}^{0}$ , step 
γ > 0, and regularization parameter $\tau>0$ 
set: t←1, s0←x0, q0 ← 1
repeat 

zt ← st−1 − γ∇D(st−1)

x ← proxR(zt, γτ)

qt←$\fra{}{}$2 (1 + √1 + 4q2−1
st ←xt +((qt−1− 1)/qt)(xt − x−1)
t←t+1

until stopping criterion 

return estimate of the refractive index $\widehat{\mathbf{x}}^{t}$ 

Algorithm 4 FGP for evaluating $\mathbf{x}=\mathrm{p r o x}_{\mathcal{R}}(\mathbf{z},\tau)$ 
input: z ∈ RN , τ > 0.

set: t ←1, d0 ← g0, q0←1,γ←1/(12τ)
repeat 

gt ← projg (dt−1 + γD (projχ ( − τDTdt−1)))
 = proj ( − τ DT gt)

$qt←\frac}{}$ (1 + √1 + 4q2−1)

dt ← gt + ((qt−1 − 1)/qt)(gt − gt−1)

t ←t + 1

until stopping criterion 

return xt 

magnitudes of the image gradient, which can also be viewed as a penalty promoting joint-sparsity of the gradient components.By promoting signals with sparse gradients, TV minimization recovers images that are piecewise-smooth, which means that they consist of smooth regions separated by sharp edges.Isotropic TV regularizer (30) is rotation invariant, which makes it preferable in the context of image reconstruction.

One must note that similar to other regularization schemes,there is, unfortunately, no theoretically optimal way of setting $\tau;$ its optimal value might depend on a number of parameters including the sample, forward model, and noise. Generally,higher levels of τ imply stronger regularization during the reconstruction and the optimal value of τ, in our experiments,was in the range $[10^{-2},\overset{\circ}{1}0^{1}]$ for the configurations considered.

### B. Minimization of TV 

Fast iterative shrinkage/thresholding algorithm (FISTA),summarized in Algorithm 3, is one of the most popular approaches for solving (5). FISTA relies on the efficient evaluation of the gradient ∇D and of the proximal operator (16).Time-reversal scheme, in Algorithm 1, makes aplication of FISTA straightforward for solving (5) with regularizers that admit closed form poximal operators such as $\ell_{1}\mathtt{-p e n a l t y}$ However, some regularizers including TV do not have closed form proximals and require an additional iterative algorithm for solving (16).



In our implementation, we solve (16) with the dual approach that was proposed by Beck and Teboulle in [25]. The approach,summarized in Algorithm 4, is based on iterative solving the dual optimization problem 

$$\widehat{\mathbf{g}}=\mathop{\operatorname{a r g}\operatorname*{m i n}}_{\mathbf{g}\in\mathcal{G}}\left\{\mathcal{Q}(\mathbf{g})\right\},$$

where 

$$\begin{aligned}{\mathcal{Q}(\mathbf{g})\triangleq}&{{}-\frac{1}{2}\|\mathbf{z}-\tau\mathbf{D}^{T}\mathbf{g}-\operatorname{p r o j}_{\mathcal{X}}(\mathbf{z}-\tau\mathbf{D}^{T}\mathbf{g})\|_{\ell_{2}}^{2}}\\ {}&{{}\quad+\frac{1}{2}\|\mathbf{z}-\tau\mathbf{D}^{T}\mathbf{g}\|_{\ell_{2}}^{2}.}\\ \end{aligned}$$

Given the dual iterate $\mathbf{g}^{t}$ , the corresponding primal iterate can be computed as 



$$\mathbf{x}^{t}=\operatorname{p r o j}_{\mathcal{X}}(\mathbf{z}-\tau\mathbf{D}^{T}\mathbf{g}^{t}).$$

The operator proj represents an orthogonal projection onto the  convex  set $\mathcal{X}$ . For example, a projection onto $N\cdot$ dimensional cube 



$$\mathcal{X}\triangleq\left\{\mathbf{x}\in\mathbb{R}^{N}:a\leq x_{n}\leq b,\forall n\in[1,\ldots,N]\right\},$$

with bounds a,$b>0$ ,is given by 

$$[\operatorname{p r o j}_{\mathcal{X}}(\mathbf{x})]_{n}=\begin{cases}{a}&{\quad\operatorname{i f}~x_{n}<a}\\ {x_{n}}&{\quad\operatorname{i f}~a\leq x_{n}\leq b}\\ {b}&{\quad\operatorname{i f}~x_{n}>b,}\\ \end{cases}$$

for all $n\in[1,\ldots,N]$ 

The  set $\mathcal{G}\subseteq\mathbb{R}^{N\times3}$ in (32) depends on the variant of TV used for regularization. For anisotropic TV (29), the set corresponds to 



$$\mathcal{G}\:\triangleq\:\{\mathbf{g}\in\mathbb{R}^{N\times3}:\|[\mathbf{g}]_{n}\|_{\ell_{\infty}}\leq1,\forall n\in[1,\ldots,N]\}$$

with the corresponding projection 

$$[\operatorname{p r o j}_{\mathcal{G}}(\mathbf{g})]_{n}=\left(\begin{matrix}{\frac{[\mathbf{g}_{x}]_{n}}{\operatorname*{m a x}(1,|[\mathbf{g}_{x}]_{n}|)}}\\ {\frac{[\mathbf{g}_{y}]_{n}}{\operatorname*{m a x}(1,|[\mathbf{g}_{y}]_{n}|)}}\\ {\frac{[\mathbf{g}_{z}]_{n}}{\operatorname*{m a x}(1,|[\mathbf{g}_{z}]_{n}|)}}\\ \end{matrix}\right),$$

for all $n\in[1,\ldots,N]$ .  Similarly, for isotropic TV (30), the set corresponds to 



$$\mathcal{G}\triangleq\{\mathbf{g}\in\mathbb{R}^{N\times3}:\|[\mathbf{g}]_{n}\|_{\ell_{2}}\leq1,\forall n\in[1,\ldots,N]\}$$

with the corresponding projection 

$$[\operatorname{p r o j}_{\mathcal{G}}(\mathbf{g})]_{n}=\frac{[\mathbf{g}]_{n}}{\operatorname*{m a x}\left(1,\|[\mathbf{g}]_{n}\|_{\ell_{2}}\right)},$$

for all $n\in[1,\ldots,N]$ 

While the theoretical convergence of FISTA requires the full convergence of inner Algorithm 4, in practice, it is sufficient to run about 5-10 iterations with an initializer that corresponds to the dual variable from the previous outer iteration. In our implementation, we thus fix the maximal number of inner iterations to $t_{\mathrm{i n}}=10$ and enforce an additional stopping criterion based on measuring the relative change of the solution in two successive iterations as $\|\mathbf{g}^{t}-\mathbf{g}^{t-1}\|_{\ell_{2}}/\|\mathbf{g}^{t-1}\|_{\ell_{2}}\leq\delta_{\mathrm{i n}}$ ,where $\delta_{\mathsf{i n}}=10^{-4}$ in all the experiments here.

## REFERENCES 

[1] A. C. Kak and M. Slaney, Principles of Computerized Tomography Imaging. IEEE, 1988.
[2] E. Wolf, "Three-dimensional structure determination of semi-transparent objects from holographic data," Opt. Commun.,vol. 1,no. 4, pp. 153–156, September/October 1969.
[3] A. J. Devaney, "Inverse-scattering theory within the Rytov approximation," Opt. Lett., vol. 6, no. 8, pp. 374–376, August1981.[4] W. Choi, C. Fang-Yen, K. Badizadegan, S. Oh, N. Lue, R. R. Dasari,and M. S. Feld,"Tomographic phase microscopy," Nat. Methods, vol. 4,no. 9, pp. 717–719, September 2007.
[5] Y. Sung, W. Choi, C. Fang-Yen, K. Badizadegan, R. R. Dasari, and M. S. Feld, "Optical diffraction tomography for high resolution live cell imaging,," Opt.Express, vol. 17,no. 1, pp. 266–27, December 2009.[6] E. J. Candes, J. Romberg, and T. Tao, "Robust uncertainty princiles:
Exact signal reconstruction from highly incomplete frequency information," IEEE Trans.Inf. Theory, vol. 52, no. 2,pp. 489-59, February 2006.
[7] D. L. Donoho, "Compressed sensing," IEEE Trans. Inf. Theory, vol. 52,
no. 4,pp.1289–1306,April 2006.
[8] M. M. Bronstein, A.M. Bronstein, M. Zibulevsky, and H. Azhari,
"Reconstruction in diffraction ultrasound tomography using nonuniform FFT,"IEEE Trans. Med. Imag., vol. 21,no. 11,pp. 1395–1401,
November 2002.
[9] Y. Sung and R. R. Dasari, "Deterministic regularization of threedimensionaloptical diffractiontomography," J.Opt.Soc.Am.A,vol.28,
no. 8, pp. 1554–1561, August 2011.
[10] H. J. Breaux, "An analysis of mathematical transformations and a comparison of numerical techniques for computation of high-energy CW laser propagation in an inhomogeneous medium,," Ballistic Research Laboratories Aberdeen Proving Ground, Maryland, Tech. Rep., June 1974.
[11] J. Wallace and J.Q. Lilly, "Thermal blooming of repetitively pulsed laser beams," J. Opt. Soc.Am., vol. 64, no. 12, 1974.[12] J.A. Fleck, J. R. Morris, and M. D. Feit, "Time-dependent propagation of high energy laser beams through the atmosphere,," Appl. Phys., vol. 10,
no. 2, pp. 129–160, June 1976.
[13] W. G. Tam, "Split-step fourier-transform analysis for laser-pulse propagation in particulate media," J. Opt. Soc. Am., vol. 72, no. 10,pp.
1311–1316,October1982.
[14] A. Goy, "Imaging and microscopy in linear and nonlinear media using digital holography," Ph.D. dissertation, École polytechnique fédérale de Lausanne, January 2013,thesis number 5617.
[15] G. Maire, F. Drsek, J. Girard, H. Giovaninni, A. Talneau, D. Konan,
K. Belkebir, P. C. Chaumet, and A. Sentenac, "Experimental demonstration of quantitative imaging beyond Abbe's limit with optical diffraction tomography,"Phys. Rev. Lett.,vol. 102,p. 213905, May 2009.[16] O. Haeberlé, K. Belkebir, H. Giovaninni, and A. Sentenac, "Tomographic diffractive microscopy: basic, techniques, and perspectives," J.
Mod. Opt., vol. 57, no. 9, pp. 686–699, May 2010.[17] U. S. Kamilov, I. N. Papadopoulos, M. H. Shoreh, A. Goy, C. Vonesch,
M. Unser, and D. Psaltis, "Learning approach to optical tomography,"
Optica, vol. 2,no. 6,pp. 517–522, June 2015.
[18] L. Tian andL.Waller,"3Dintensity and phase imaging from light field measurements in an LED array microscope,," Optica, vol. 2, pp. 104–
111,2015.
[19] I. Yamaguchi and T. Zhang, "Phase-shifting digital horography," Opt.
Lett., vol. 22, pp. 1268–1270, 1997.
[20] U. Schnars and W. Jueptner, Digital Horography. Springer, 2005.[21] L.I. Rudin,S.Osher, and E.Fatemi,"Nonlinear total variation based noise removal algorithms," Physica D, vol. 60, no. 1–4, pp. 259–268,
November 1992.
[22] M. Unser and P. Tafti,AnIntroduction to Sparse Stochastic Processes.
Cambridge Univ. Press, 2014.
[23]E. Bostan, U. S. Kamilov, M. Nilchian, and M. Unser, "Sparse stochastic processes and discretization of linear inverse problems, IEEE Trans.
Image Process., vol. 22, no. 7, pp. 2699–2710, July 2013.[24]C. M. Bishop, Neural Networks for Pattern Recognition. Oxford, 1995.[25]A. Beck and M. Teboulle, "Fast gradient-based algorithm for constrained total variation image denoising and deblurring problems,," IEEE Trans.
Image Process., vol. 18, no. 11, pp. 2419–2434, November 2009.[26]D.P.Bertsekas,"Incrementalproximal methods for largescaleconvex optimization," Math. Program.Ser. B,vol.129, pp.163–195, 2011.[27]M.V. Afonso, J. M.Bioucas-Dias, and M. A.T.Figueiredo, "Fast image recovery using variable splitting and constrained optimization," IEEE Trans. Image Process.,vol. 19,no. 9,pp. 2345–2356, September 2010.

[28]U.S.Kalov,E.Boa,an MUnr,"Viaioaljusticoof cycle spinning for wavelet-based solutionsof inverse problems," EEE Signal Process.Lett.,vol.21,o.11, pp.1321330,November01.[29] Z. Qin, D. Goldfarb, and S. Ma, "An alternating direction method for total variation denoising," Optim. Method Softw., vol. 30, no. 3, pp.594–615, 2015.
[30] A. Bourquard, N. Pavillon, E. Bostan, C. Depeursinge, and M. Unser,
"A practical inverse-problem approach to digital holographic reconstruction," Opt. Express,vol. 21, no. 3, pp. 3417–3433, February 2013.[31] T. Kim, R. Zhou, M. Mir, S. Babacan, P. Carney, L. Goddard, and G. Popescu, "White-light diffraction tomography of unlabelled live cells,"Nat. Photonics,vol.8,pp. 256–263, March 2014.[32] Y.LeCun, Y.Bengio, and G.Hinton, "Deep learning," Nature, vol. 521,
pp. 436–444, May 28, 2015.
[33] J. W. Goodman, Introduction to Fourier Optics, 2nd ed. McGraw-Hill,
1996.
[34] M. D. Feit and J. A. Fleck, "Bean nonparaxiality,filament formaform,
and beam breakup in the self-focusing of optical beams," J. Opt. Soc.
Am.B,vol. 5,no.3,pp. 633–640, March 1988.
[35] B. Saleh and M. Teich, Fundamentals of Photonics, 2nd ed. John Wiley &Sons,207.
[36] R. Gilmore, "Baker-Campbell-Hausdorff formulas," J. Math. Phys.,
vol. 15,pp. 2090–2092, 1974.
