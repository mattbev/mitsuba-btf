import drjit as dr
import numpy as np
import mitsuba as mi


from .utils.btf_interpolator import BTFInterpolator
from .utils.coord_system_transfer import mirror_uv, orthogonal2spherical


class MeasuredBTF(mi.BSDF):
    def __init__(self, props):
        mi.BSDF.__init__(self, props)

        # BTDFFのzipファイルのパス
        self.m_filename = props["filename"]

        # 逆ガンマ補正をかけるかどうか
        if props.has_property("apply_inv_gamma"):
            self.m_apply_inv_gamma = props["apply_inv_gamma"]
        else:
            self.m_apply_inv_gamma = True

        # 反射率
        if props.has_property("reflectance"):
            self.m_reflectance = mi.Float(props["reflectance"])
        else:
            self.m_reflectance = mi.Float(1.0)

        # Power parameter
        if props.has_property("power_parameter"):
            self.m_power_parameter = mi.Float(props["power_parameter"])
        else:
            self.m_power_parameter = mi.Float(4.0)

        # Wrap mode
        if props.has_property("wrap_mode"):
            self.m_wrap_mode = str(props["wrap_mode"])
        else:
            self.m_wrap_mode = "repeat"

        # UVマップの変換
        # a = mi.Transform3f
        m_transform = props["to_uv"].extract()
        if isinstance(m_transform, mi.Transform3f):
            self.m_transform = mi.Transform3f(m_transform)
        else:
            self.m_transform = mi.Transform3f(m_transform.matrix)

        # 読み込んだBTF
        self.btf = BTFInterpolator(self.m_filename, p=self.m_power_parameter)

        self.m_flags = mi.BSDFFlags.DiffuseReflection | mi.BSDFFlags.FrontSide
        self.m_components = [self.m_flags]


    def get_btf(self, wi, wo, uv):
        """
        BTFの生の値を取得する

        wi : enoki.scalar.Vector3f
            Incident direction

        wo : enoki.scalar.Vector3f
            Outgoing direction

        uv : enoki.scalar.Vector2f
            UV surface coordinates
        """
        print("HERE")
        # カメラ側の方向
        _, tv, pv = orthogonal2spherical(*wi)

        # 光源側の方向
        _, tl, pl = orthogonal2spherical(*wo)

        # 画像中の座標位置を求める
        uv = self.m_transform.transform_affine(uv)

        # warp_modeがmirrorなら座標の変換
        if self.m_wrap_mode == "mirror":
            uv = mirror_uv(uv).T

        u, v = uv

        # BTFの画素値を取得
        bgr = self.btf.angles_uv_to_pixel(tl, pl, tv, pv, u, v)

        # 0.0~1.0にスケーリング
        bgr = np.clip(bgr / 255.0 * self.m_reflectance, 0, 1)

        # 逆ガンマ補正をかける
        if self.m_apply_inv_gamma:
            bgr **= 2.2

        return mi.Vector3f(bgr[..., ::-1])


    def sample(self, ctx, si, sample1, sample2, active):
        """
        BSDF sampling
        """
        cos_theta_i = mi.Frame3f.cos_theta(si.wi)

        active &= cos_theta_i > 0

        bs = mi.BSDFSample3f()
        bs.wo = mi.warp.square_to_cosine_hemisphere(sample2)
        bs.pdf = mi.warp.square_to_cosine_hemisphere_pdf(bs.wo)
        bs.eta = 1.0
        bs.sampled_type = mi.BSDFFlags.DiffuseReflection
        bs.sampled_component = 0

        value = self.get_btf(si.wi, bs.wo, si.uv) / mi.Frame3f.cos_theta(bs.wo)

        return (bs, dr.select(active & (bs.pdf > 0.0), value, mi.Vector3f(0)))


    def eval(self, ctx, si, wo, active):
        """
        Emitter sampling
        """
        if not ctx.is_enabled(mi.BSDFFlags.DiffuseReflection):
            return mi.Vector3f(0)

        cos_theta_i = mi.Frame3f.cos_theta(si.wi)
        cos_theta_o = mi.Frame3f.cos_theta(wo)

        value = self.get_btf(si.wi, wo, si.uv) * mi.Float(1 / np.pi)

        return dr.select((cos_theta_i > 0.0) & (cos_theta_o > 0.0), value, mi.Vector3f(0))


    def pdf(self, ctx, si, wo, active):
        if not ctx.is_enabled(mi.BSDFFlags.DiffuseReflection):
            return mi.Vector3f(0)

        cos_theta_i = mi.Frame3f.cos_theta(si.wi)
        cos_theta_o = mi.Frame3f.cos_theta(wo)

        pdf = mi.warp.square_to_cosine_hemisphere_pdf(wo)

        return dr.select((cos_theta_i > 0.0) & (cos_theta_o > 0.0), pdf, 0.0)
