import { renderHook, waitFor } from "@testing-library/react";
import { useAuthCheck } from "@/hooks/useAuthCheck";
import { useRouter } from "next/navigation";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

describe("useAuthCheck", () => {
  let replaceMock: jest.Mock;

  beforeEach(() => {
    replaceMock = jest.fn();
    (useRouter as jest.Mock).mockReturnValue({ replace: replaceMock });

    localStorage.clear();
    jest.restoreAllMocks();

    if (!globalThis.fetch) {
      globalThis.fetch = jest.fn();
    }
  });

  it("redirects to '/' if no token", async () => {
    const { result } = renderHook(() => useAuthCheck());
    expect(replaceMock).toHaveBeenCalledWith("/");
    expect(result.current).toBe(false);
  });

  it("sets authChecked true if token valid", async () => {
    localStorage.setItem("token", "fake-token");

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
    } as Response);

    const { result } = renderHook(() => useAuthCheck());

    await waitFor(() => {
      expect(result.current).toBe(true);
    });
  });

  it("removes token and redirects if token invalid", async () => {
    localStorage.setItem("token", "fake-token");

    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: false,
    } as Response);

    const { result } = renderHook(() => useAuthCheck());

    await waitFor(() => {
      expect(localStorage.getItem("token")).toBe(null);
      expect(replaceMock).toHaveBeenCalledWith("/");
    });
  });
});
