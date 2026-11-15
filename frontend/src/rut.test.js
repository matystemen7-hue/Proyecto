import { describe, expect, it } from "vitest";
import { formatRut, isValidIpe, isValidRut } from "./rut";

describe("RUT", () => {
  it("acepta RUT válidos con y sin puntos", () => {
    expect(isValidRut("12.345.678-5")).toBe(true);
    expect(isValidRut("123456785")).toBe(true);
  });
  it("rechaza dígito verificador incorrecto", () => {
    expect(isValidRut("12.345.678-9")).toBe(false);
  });
  it("rechaza vacío o basura", () => {
    expect(isValidRut("")).toBe(false);
    expect(isValidRut("abc")).toBe(false);
  });
  it("formatea con guion", () => {
    expect(formatRut("12.345.678-5")).toBe("12345678-5");
  });
});

describe("IPE", () => {
  it("valida 8 a 12 caracteres alfanuméricos", () => {
    expect(isValidIpe("100200300")).toBe(true);
    expect(isValidIpe("12")).toBe(false);
    expect(isValidIpe("1002 00300")).toBe(false);
  });
});
