# Smode IK Rig & IK Deform

*[Version française](README.fr.md)*

> **Experimental, not an official Smode tool.** Built by trial and error against the Oil API (see [smode-oil-reference](https://github.com/gyomh/smode-oil-reference)). Tested on Smode Compose R15.

Two Smode Scripts for character / object rigging, inspired by [Duik](https://rxlaboratory.org/tools/duik/)
(RxLaboratory):

- **IK Rig** (`IK_Rig_GYOMH.py`): an IK / FK chain of 2 to 12 bones that **moves your own 3D elements** (an arm, a leg,
  a tentacle...). Handles drive the chain; the elements follow.
- **IK Deform** (`IK_Deform_GYOMH.py`): the same rig, but it **deforms one 3D object** (capsule, cylinder, sphere, box,
  plane, rectangle, torus, circle, star) with one `Transform3dGeometryModifier` per joint and a linear mask for a soft
  bend (linear blend skinning in an FK chain).

## Install

1. Drag the Script into your Smode project and set its **Launch Mode** to **At Every Update**.
2. Outside a 3D Group the Script **creates its own Group and moves itself into it**. Rigs can be nested in groups
   (body > arms, legs).
3. **Drag your 3D elements into the group** (IK Rig: the bones, 2 to 12; IK Deform: the object to deform). With
   *Auto Rig* on, the rig is created by itself; otherwise fill the *Object* / *Bone n* fields and click **Create Rig**.

## What you get

- Handles (icon planes, always facing the Compo camera): `IK_Joint_1..N` and `IK_Cible` (the tip target).
- Two Parameter Banks: **1 - Manual Setup tools** (Auto Rig, 2D Mode, Bone Count, IK1 Angle Min/Max, Bone / Object,
  Limit 180° between each pair of bones, Create Rig, Setup Pivots, RESET) and **2 - Animation tools** (Show Joints,
  FK Mode, one **Flip Bend** per joint; IK Rig also has `Bone# Rotation`).
- **IK / FK**: pull a joint in IK (the tip stays on the target) or FK (the following bones and the target follow).
- **2D / 3D**: planar mode keeps the whole chain in the root plane.
- **Limit 180°**: a joint can only bend one way. **IK1 Angle Min / Max** limits the first bone.
- **Setup Pivots**: freely move the handles onto the real joints, untick to validate.
- **RESET** (red button): removes the rig, restores every parameter and goes back to manual mode.
- Works with animation (keyframes on the handles) and can be nested.

## Notes

- Angles in the Script's own parameters are in **radians** (the Banks show degrees).
- **Imported meshes (FBX / OBJ...) work in IK Rig** (V1.16): the bone axis is **Y** with the pivot at the base, like a capsule,
  so export your pieces with each pivot on its joint and the bone running along +Y. The length of a bone is the distance to the
  next one, but the **last bone's length cannot be read from an imported mesh**: set **Last Bone Length (imported)** in the
  *Manual Setup* bank (0 = same length as the previous bone), then click Create Rig again.
- IK Deform needs enough subdivisions along the object: it raises *Height Precision* / *Precision* automatically and
  RESET restores them. Imported meshes are **not supported yet** (unknown objects fall back to the Y axis, 1 m, with a
  warning). The cylinder pivot and the sphere / torus orientation are assumptions, please report a mismatch.
- Hide the handles (**Show Joints** off) before rendering; a red text reminds you while they are visible.

## License

MIT — see [LICENSE](LICENSE).
