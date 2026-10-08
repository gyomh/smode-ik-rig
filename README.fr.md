# Smode IK Rig & IK Deform

*[English version](README.md)*

> **Expérimental, pas un outil officiel Smode.** Construit par essais et erreurs sur l'API Oil (voir [smode-oil-reference](https://github.com/gyomh/smode-oil-reference)). Testé sur Smode Compose R15.

Deux Scripts Smode de rigging pour personnage / objet, inspirés de [Duik](https://rxlaboratory.org/tools/duik/)
(RxLaboratory) :

- **IK Rig** (`IK_Rig_GYOMH.py`) : une chaîne IK / FK de 2 à 12 bones qui **déplace vos propres éléments 3D** (un bras,
  une jambe, un tentacule...). Des poignées pilotent la chaîne, les éléments suivent.
- **IK Deform** (`IK_Deform_GYOMH.py`) : le même rig, mais qui **déforme un objet 3D** (capsule, cylindre, sphère,
  boîte, plan, rectangle, torus, cercle, étoile) avec un `Transform3dGeometryModifier` par articulation et un masque
  linéaire pour un pli doux (skinning linéaire en chaîne FK).

## Installation

1. Glissez le Script dans votre projet Smode et mettez son **Launch Mode** sur **At Every Update**.
2. Hors d'un Group 3D, le Script **crée son propre Group et s'y place**. Les rigs peuvent être imbriqués
   (corps > bras, jambes).
3. **Glissez vos éléments 3D dans le groupe** (IK Rig : les bones, 2 à 12 ; IK Deform : l'objet à déformer). Avec
   *Auto Rig* activé, le rig se crée tout seul ; sinon remplissez les champs *Object* / *Bone n* et cliquez sur
   **Create Rig**.

## Ce que vous obtenez

- Des poignées (plans à icône, toujours face à la caméra de la Compo) : `IK_Joint_1..N` et `IK_Cible` (la cible de
  la pointe).
- Deux Parameter Banks : **1 - Manual Setup tools** (Auto Rig, 2D Mode, Bone Count, IK1 Angle Min/Max, Bone / Object,
  Limit 180° entre chaque paire de bones, Create Rig, Setup Pivots, RESET) et **2 - Animation tools** (Show Joints,
  FK Mode, un **Flip Bend** par articulation ; IK Rig a aussi `Bone# Rotation`).
- **IK / FK** : tirez une articulation en IK (la pointe reste sur la cible) ou en FK (les bones suivants et la cible
  suivent).
- **2D / 3D** : le mode planar garde toute la chaîne dans le plan de la racine.
- **Limit 180°** : une articulation ne plie que dans un sens. **IK1 Angle Min / Max** limite le premier bone.
- **Setup Pivots** : placez librement les poignées sur les vraies articulations, décochez pour valider.
- **RESET** (bouton rouge) : supprime le rig, remet tous les paramètres et repasse en mode manuel.
- Compatible avec l'animation (clés sur les poignées) et imbriquable.

## Notes

- Les angles des paramètres du Script sont en **radians** (les Banks affichent des degrés).
- **Les maillages importés (FBX / OBJ...) fonctionnent dans IK Rig** (V1.16) : l'axe d'un bone est **Y**, pivot à la base, comme une
  capsule ; exportez donc vos pièces avec chaque pivot sur son articulation et le bone orienté le long de +Y. La longueur d'un bone est
  la distance au suivant, mais celle du **dernier bone ne peut pas être lue sur un maillage importé** : réglez **Last Bone Length
  (imported)** dans le bank *Manual Setup* (0 = même longueur que le bone précédent), puis recliquez sur Create Rig.
- IK Deform a besoin de subdivisions suffisantes le long de l'objet : il augmente *Height Precision* / *Precision*
  automatiquement et RESET les restaure. Les maillages importés ne sont **pas encore gérés** (un objet inconnu prend
  l'axe Y, 1 m, avec un avertissement). Le pivot du cylindre et l'orientation de la sphère / du torus sont des
  hypothèses, signalez tout écart.
- Masquez les poignées (**Show Joints** décoché) avant le rendu ; un texte rouge le rappelle tant qu'elles sont
  visibles.

## Licence

MIT — voir [LICENSE](LICENSE).
