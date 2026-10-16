import { expect, test } from "vitest";
import { FORMA_PROPS } from "@/lib/contrato";
import bff from "./contrato-bff.json";

/**
 * Props de cada bloco iguais no BFF e no front, campo a campo e em todos os
 * niveis. `tsc` amarra FORMA_PROPS aos tipos de `sdui.ts`; aqui ela encontra a
 * forma exportada do Pydantic. Falhou? Ou o contrato mudou de um lado so, ou
 * faltou `python -m scripts.forma_contrato`.
 */
test("props do contrato iguais no Pydantic e no espelho TS", () => {
  expect(FORMA_PROPS).toEqual(bff);
});
