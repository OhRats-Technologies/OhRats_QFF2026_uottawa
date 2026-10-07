// Original deterministic assets: painted metal grain and layered pine/fire silhouette.
export function createArt() {
  const metal = document.createElement("canvas");
  metal.width = 128;
  metal.height = 128;
  const m = metal.getContext("2d");
  m.fillStyle = "#123638";
  m.fillRect(0, 0, 128, 128);
  let seed = 163;
  const random = () => {
    seed = (seed * 16807) % 2147483647;
    return seed / 2147483647;
  };
  for (let i = 0; i < 2400; i++) {
    m.fillStyle = random() > 0.5 ? "#aedbb40b" : "#00000015";
    m.fillRect(random() * 128, random() * 128, random() * 5 + 1, 1);
  }
  return { metal };
}

export async function loadAssets() {
  const art = createArt();
  const image = async (src) => {
    const img = new Image();
    img.src = src;
    await img.decode();
    return img;
  };
  const [cover, map, forest] = await Promise.all([
    image("../presentation/assets/ontario-cover.png"),
    fetch("../presentation/assets/map.json").then((r) => r.json()),
    image("./canvas/forest.png"),
  ]);
  return { ...art, cover, map, forest };
}
